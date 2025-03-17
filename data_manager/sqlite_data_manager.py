import sqlite3
import logging  # For error handling
import requests


class SQLiteDataManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self):
        """Create the users and movies tables if they don't exist."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Check if the users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            users_table_exists = cursor.fetchone() is not None

            # Check if the movies table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
            movies_table_exists = cursor.fetchone() is not None

            if not users_table_exists:
                cursor.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL
                    )
                """)
                print("Created users table")

            if not movies_table_exists:
                cursor.execute("""
                    CREATE TABLE movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        director TEXT,
                        plot TEXT,
                        poster TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                print("Created movies table")

            conn.commit()
            print("Tables checked.")

        except sqlite3.Error as e:
            logging.exception(f"Error creating tables: {e}")
        finally:
            if conn:
                conn.close()

    def fetch_movie_details_from_omdb(self, title):
        """Fetch movie details from OMDb API using the movie title."""
        api_key = 'c24302'  # Replace with your OMDb API key
        url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"

        response = requests.get(url)

        if response.status_code == 200:
            movie_data = response.json()
            if movie_data['Response'] == 'True':
                return movie_data
            else:
                raise ValueError("Movie not found in OMDb.")
        else:
            raise Exception("Failed to fetch data from OMDb API.")


    def get_all_users(self):
        """Fetch all users from the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users")
            users = []
            for row in cursor.fetchall():
                user = {'id': row['id'], 'username': row['username']}
                users.append(user)
            return users
        except sqlite3.Error as e:
            logging.exception(f"Error fetching users")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        """Fetch a user by their ID."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return user
        except sqlite3.Error as e:
            logging.exception(f"Error fetching user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_user(self, username):
        """Add a new user to the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            print(f"Added user: {username}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Error adding user: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_movies_for_user(self, user_id):
        """Fetch all movies for a specific user."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE user_id = ?", (user_id,))
            movies = cursor.fetchall()
            return movies
        except sqlite3.Error as e:
            logging.exception(f"Error fetching movies: {e}")
            return []
        finally:
            if conn:
                conn.close()


    def add_movie(self, user_id, title, director, plot, poster):
        """Add a new movie to a user's list."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Fetch movie details from OMDb API
            omdb_movie_details = self.fetch_movie_details_from_omdb(title)
            title = omdb_movie_details.get('Title', title)  # Use OMDb title if available
            director = omdb_movie_details.get('Director', director)  # Use OMDb director if available
            plot = omdb_movie_details.get('Plot', plot)  # Use OMDb plot if available
            poster = omdb_movie_details.get('Poster', poster)  # Use OMDb poster if available

            cursor.execute("INSERT INTO movies (user_id, title, director, plot, poster) VALUES (?, ?, ?, ?, ?)",
                           (user_id, title, director, plot, poster))
            conn.commit()
            print(f"Added movie: {title} for user {user_id}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Error adding movie: {e}")
            return False
        except Exception as e:
            logging.exception(f"Error fetching OMDb movie details: {e}")
            return False
        finally:
            if conn:
                conn.close()


    def get_movie_by_id(self, movie_id):
        """Fetch a movie by its ID."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            movie = cursor.fetchone()
            return movie
        except sqlite3.Error as e:
            logging.exception(f"Error fetching movie: {e}")
            return None
        finally:
            if conn:
                conn.close()


    def update_movie(self, movie_id, title, director, plot, poster, rating):
        """Update details of a specific movie."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE movies 
                SET title = ?, director = ?, plot = ?, poster = ?, rating = ? 
                WHERE id = ?
            """, (title, director, plot, poster, rating, movie_id))
            conn.commit()
            print(
                f"Updated movie {movie_id} to title: {title}, director: {director}, plot: {plot}, poster: {poster}, rating: {rating}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Error updating movie: {e}")
            return False
        finally:
            if conn:
                conn.close()


    def delete_movie(self, movie_id):
        """Delete a specific movie from the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            conn.commit()
            print(f"Deleted movie: {movie_id}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Error deleting movie: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        """Delete a specific user from the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            print(f"Deleted user: {user_id}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Error deleting user: {e}")
            return False
        finally:
            if conn:
                conn.close()