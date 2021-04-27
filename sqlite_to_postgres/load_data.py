import json
import logging
import re
import sqlite3
import uuid

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from models import FilmWork


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """
    Convert fetched data row from tuple to dict
    :param cursor: sqlite3 cursor
    :param row: tuple of row values
    :return: d: dict like {field_name: field_value}
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteLoader:
    """
    This class allows you to extract data from badly designed db.sqlite
    """
    connection: sqlite3.Connection

    def __init__(self, connection: sqlite3.Connection):
        connection.row_factory = dict_factory
        self.connection = connection
        self.cursor = connection.cursor()

    def load_all_data(self):
        """
        Loads data from db.sqlite into memory
        :return:
        movies: list[FilmWork] with extracted movies,
        movie_persons: list of dicts with information about m2m movies to person relations,
        movie_genres: list of dicts with information about m2m genres to person relations,
        person_uuid: dict like {person_name_1: person_uuid_1, ...},
        genre_uuid: dict like {genre_1: genre_uuid_1, ...}
        """
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
                    # some directors have unnecessary comment
                    director_name = re.sub("[\(\[].*?[\)\]]", "", director_name)

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
        # get rid of N/A persons
        movie_persons = [person for person in movie_persons if person["name"] != "N/A"]

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
        Combine writer ids to one collection from two fields
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
    """
    The class allows you to save data to PostgreSQL database
    """
    connection: _connection

    def __init__(self, pg_conn):
        self.connection = pg_conn

    def save_data(self, data):
        """
        save data to PostgreSQL
        :param data: data returned from SQLiteLoader.load_all_data
        :return: None
        """
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
    """Main function which transfers data from SQLite to Postgres"""
    sqlite_loader = SQLiteLoader(connection)
    data = sqlite_loader.load_all_data()

    postgres_saver = PostgresSaver(pg_conn)
    postgres_saver.save_data(data)


if __name__ == '__main__':
    dsl = {'dbname': 'movies',
           'user': 'django',
           'password': 'password',
           'host': '127.0.0.1',
           'port': 5432}
    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
