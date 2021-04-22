CREATE DATABASE movies;
\c movies;
CREATE SCHEMA IF NOT EXISTS content;

SET search_path TO content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    imdb_rating FLOAT
);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
    genre TEXT NOT NULL
);

CREATE TYPE job AS ENUM ('actor', 'writer', 'director');
CREATE TABLE IF NOT EXISTS content.film_work_person (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    person_id uuid NOT NULL,
    job job NOT NULL,
    FOREIGN KEY (film_work_id)
        REFERENCES film_work(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id)
        REFERENCES person(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS content.film_work_genre (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    genre_id uuid NOT NULL,
    FOREIGN KEY (film_work_id)
        REFERENCES film_work(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id)
        REFERENCES genre(id) ON DELETE CASCADE
);
