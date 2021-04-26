import json
import logging
import psycopg2
import sqlite3
import uuid

from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from sqlite_to_postgres.models import FilmWork


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# TODO: document it all
class SQLiteLoader:
    connection: sqlite3.Connection

    def __init__(self, connection: sqlite3.Connection):
        connection.row_factory = dict_factory
        self.connection = connection
        self.cursor = connection.cursor()

    def load_all_data(self):
        sql = "SELECT * FROM movies"
        movies = []
        movie_persons = []
        movie_genres = []
        movie_id_uuid = dict()
        for row in self.cursor.execute(sql):
            self._validate_na(row)

            # assign brand new uuid and remove ugly old id
            movie_uuid = uuid.uuid4()
            row["uuid"] = movie_uuid
            movie_id_uuid[row["id"]] = movie_uuid
            row.pop("id")

            # ratings are None anyway
            row.pop("ratings")

            # fill persons list
            writer_ids = self._combine_writers(row)
            row.pop("writer")
            row.pop("writers")
            for writer_id in writer_ids:
                movie_persons.append({"movie_uuid": movie_uuid,
                                      "id": writer_id,
                                      "name": None,
                                      "role": "writer"})

            directors = row.pop("director")
            if directors:
                for director_name in directors.split(', '):
                    movie_persons.append({"movie_uuid": movie_uuid,
                                          "id": None,
                                          "name": director_name,
                                          "role": "director"})

            genres = row.pop("genre")
            if genres:
                for genre in genres.split(', '):
                    movie_genres.append({"movie_uuid": movie_uuid, "genre": genre})

            film_work = FilmWork(title=row["title"],
                                 id=row["uuid"],
                                 description=row["plot"],
                                 imdb_rating=row["imdb_rating"])
            movies.append(film_work)

        # get writer names from writers table
        sql_writers = """SELECT name FROM writers WHERE id=(?);"""
        for person in movie_persons:
            if person["role"] == "writer":
                self.cursor.execute(sql_writers, (person["id"],))
                row = self.cursor.fetchone()
                person["name"] = row["name"]

        # get rid of N/A writer
        movie_persons = [person for person in movie_persons if person["name"] != "N/A"]

        sql_movie_actors = """
                           SELECT movies.id, actors.name 
                           FROM actors 
                           INNER JOIN movie_actors ma ON actors.id = ma.actor_id
                           INNER JOIN movies ON movies.id = ma.movie_id;
                           """
        for row in self.cursor.execute(sql_movie_actors):
            movie_persons.append({"movie_uuid": movie_id_uuid[row["id"]],
                                  "name": row["name"],
                                  "role": "actor"})

        # get unique persons (by unique name) and assign uuids
        unique_persons = set()
        for person in movie_persons:
            unique_persons.add(person["name"])
        person_uuid = {person: uuid.uuid4() for person in unique_persons}

        # get unique genres and assign uuids
        unique_genres = set()
        for genre in movie_genres:
            unique_genres.add(genre["genre"])
        genre_uuid = {genre: uuid.uuid4() for genre in unique_genres}
        return movies, movie_persons, movie_genres, person_uuid, genre_uuid

    @staticmethod
    def _validate_na(row: dict):
        """
        Replace "N/A" values with None
        :param row: dict corresponding to 'movies' table row
        :return: None
        """
        for key in row:
            if row[key] == "N/A":
                row[key] = None

    @staticmethod
    def _combine_writers(row: dict) -> list:
        """

        :param row: dict corresponding to `movies` table row
        :return: list[str] of writer ids
        """
        writer_ids = []
        if row["writers"]:
            writer_ids.extend((item["id"] for item in json.loads(row["writers"])))
        if row["writer"]:
            writer_ids.append(row["writer"])
        return writer_ids


class PostgresSaver:
    connection: _connection

    def __init__(self, pg_conn):
        self.connection = pg_conn

    def save_data(self, data):
        # TODO: use dataclasses
        # TODO: support executemany
        # TODO: load in batches
        movies, movie_persons, movie_genres, person_uuid, genre_uuid = data

        # clear tables. tables with m2m relation info are removed by CASCADE
        cursor = self.connection.cursor()
        cursor.execute("""
        SET search_path TO content;
        TRUNCATE film_work CASCADE;
        TRUNCATE genre CASCADE;
        TRUNCATE person CASCADE;                            
        """)

        # fill film_work
        sql = """INSERT INTO film_work(id, title, description, imdb_rating) 
                           VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;"""
        for movie in movies:
            cursor.execute(sql, (str(movie.id), movie.title, movie.description, movie.imdb_rating))
        logging.info("Uploaded all data to PostgreSQL table 'film_work'")

        # fill genre
        sql = "INSERT INTO genre(id, genre) VALUES (%s, %s);"
        for genre, genre_id in genre_uuid.items():
            cursor.execute(sql, (str(genre_id), genre))
        logging.info("Uploaded all data to PostgreSQL table 'genre'")

        # fill person
        sql = "INSERT INTO person(id, name) VALUES (%s, %s);"
        for name, person_id in person_uuid.items():
            cursor.execute(sql, (str(person_id), name))
        logging.info("Uploaded all data to PostgreSQL table 'person'")

        # fill m2m film_work_genre
        sql = "INSERT INTO film_work_genre(id, film_work_id, genre_id) VALUES (%s, %s, %s)"
        for row in movie_genres:
            values = (str(uuid.uuid4()), str(row["movie_uuid"]), str(genre_uuid[row["genre"]]))
            cursor.execute(sql, values)
        logging.info("Uploaded all data to PostgreSQL table 'film_work_genre'")

        # fill m2m film_work_person
        sql = "INSERT INTO film_work_person(id, film_work_id, person_id, job) VALUES (%s, %s, %s, %s)"
        for row in movie_persons:
            values = (str(uuid.uuid4()), str(row["movie_uuid"]), str(person_uuid[row["name"]]), row["role"])
            cursor.execute(sql, values)
        logging.info("Uploaded all data to PostgreSQL table 'film_work_person'")


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    sqlite_loader = SQLiteLoader(connection)
    data = sqlite_loader.load_all_data()

    postgres_saver = PostgresSaver(pg_conn)
    postgres_saver.save_data(data)


if __name__ == '__main__':
    dsl = {'dbname': 'movies',
           'user': 'postgres',
           'password': 'password',
           'host': '127.0.0.1',
           'port': 5432}
    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
