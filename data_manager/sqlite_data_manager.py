import sqlite3
import logging
import requests
import os

# Custom Exception for OMDb Errors
class OMDbException(Exception):
    """Custom exception for OMDb API related errors."""
    pass

class SQLiteDataManager:
    def __init__(self, db_file):
        """Initializes the data manager, sets up API key, and ensures tables exist."""
        self.db_file = db_file
        self.omdb_api_key = os.environ.get('OMDB_API_KEY')
        if not self.omdb_api_key:
             logging.warning("OMDB_API_KEY environment variable not set. Movie fetching via API will fail.")
        self.create_tables()

    def _get_connection(self):
        """Helper method to establish a database connection."""
        try:
            conn = sqlite3.connect(self.db_file, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            logging.exception(f"Database connection error to {self.db_file}: {e}")
            raise

    def create_tables(self):
        """Creates the 'users' and 'movies' tables if they do not already exist."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                )
            """)
            logging.info("Checked/Created 'users' table.")

            # --- ADDED year COLUMN ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    director TEXT,
                    year INTEGER,      -- ADDED: Store the release year as an integer
                    plot TEXT,
                    poster TEXT,
                    rating REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            logging.info("Checked/Created 'movies' table with 'year' column.")

            conn.commit()

        except sqlite3.Error as e:
            logging.exception(f"Database error during table creation: {e}")
        finally:
            if conn:
                conn.close()

    def fetch_movie_details_from_omdb(self, title):
        """Fetches movie details from OMDb API using the movie title."""
        # ... (rest of fetch logic remains the same) ...
        if not self.omdb_api_key:
             raise OMDbException("OMDb API key is not configured.")
        if not title:
             raise ValueError("Movie title cannot be empty for OMDb lookup.")

        url = f"http://www.omdbapi.com/?t={title}&apikey={self.omdb_api_key}"
        logging.info(f"Fetching data from OMDb for title: {title}")

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            movie_data = response.json()

            if movie_data.get('Response') == 'True':
                logging.info(f"Successfully fetched data for: {movie_data.get('Title')}")
                return movie_data
            elif movie_data.get('Error') == 'Movie not found!':
                logging.warning(f"Movie not found in OMDb for title: {title}")
                raise OMDbException(f"Movie '{title}' not found in OMDb.")
            else:
                error_message = movie_data.get('Error', 'Unknown OMDb API error')
                logging.error(f"OMDb API Error for title '{title}': {error_message}")
                raise OMDbException(f"OMDb API Error: {error_message}")

        except requests.exceptions.Timeout:
            logging.error(f"Timeout connecting to OMDb API for title '{title}'.")
            raise OMDbException("Request to OMDb API timed out.")
        except requests.exceptions.RequestException as e:
             logging.error(f"Network or HTTP error fetching OMDb data: {e}")
             raise OMDbException(f"Failed to connect to OMDb API: {e}")
        except Exception as e:
             logging.exception(f"Unexpected error during OMDb fetch for title '{title}': {e}")
             raise OMDbException(f"An unexpected error occurred fetching movie data: {e}")


    def get_all_users(self):
        """Fetches all users from the database, ordered by username."""
        # ... (no changes needed) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()
            return [dict(user) for user in users]
        except sqlite3.Error as e:
            logging.exception(f"Database error fetching all users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        """Fetches a single user by their ID."""
        # ... (no changes needed) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except sqlite3.Error as e:
            logging.exception(f"Database error fetching user ID {user_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_user(self, username):
        """Adds a new user to the database."""
        # ... (no changes needed) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            logging.info(f"Added user: {username} (ID: {cursor.lastrowid})")
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"Attempted to add duplicate username: {username}")
            return False
        except sqlite3.Error as e:
            logging.exception(f"Database error adding user '{username}': {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_movies_for_user(self, user_id):
        """Fetches all movies for a specific user, ordered by title."""
        # ... (no changes needed to the query itself) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE user_id = ? ORDER BY title", (user_id,))
            movies = cursor.fetchall()
            return [dict(movie) for movie in movies]
        except sqlite3.Error as e:
            logging.exception(f"Database error fetching movies for user ID {user_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # --- MODIFIED add_movie to include year ---
    def add_movie(self, user_id, title, director, year, plot, poster, rating): # Added 'year' parameter
        """Adds a new movie record to the database."""
        conn = None
        sql = """
            INSERT INTO movies (user_id, title, director, year, plot, poster, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """ # Added 'year' column and '?' placeholder
        params = (user_id, title, director, year, plot, poster, rating) # Added 'year' to params tuple
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            logging.info(f"Added movie '{title}' (ID: {cursor.lastrowid}) for user ID {user_id}")
            return True
        except sqlite3.Error as e:
            logging.exception(f"Database error adding movie '{title}' for user ID {user_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_movie_by_id(self, movie_id):
        """Fetches a single movie by its ID."""
         # ... (no changes needed to the query itself) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            movie = cursor.fetchone()
            return dict(movie) if movie else None
        except sqlite3.Error as e:
            logging.exception(f"Database error fetching movie ID {movie_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # --- MODIFIED update_movie to include year ---
    def update_movie(self, movie_id, title, director, year, plot, poster, rating): # Added 'year' parameter
        """Updates details of a specific movie."""
        conn = None
        sql = """
            UPDATE movies
            SET title = ?, director = ?, year = ?, plot = ?, poster = ?, rating = ?
            WHERE id = ?
        """ # Added 'year = ?'
        params = (title, director, year, plot, poster, rating, movie_id) # Added 'year' to params tuple
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"Updated movie ID {movie_id} with title: {title}")
                return True
            else:
                logging.warning(f"Attempted to update movie ID {movie_id}, but no matching record found.")
                return False
        except sqlite3.Error as e:
            logging.exception(f"Database error updating movie ID {movie_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_movie(self, movie_id):
        """Deletes a specific movie from the database."""
        # ... (no changes needed) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"Deleted movie ID: {movie_id}")
                return True
            else:
                logging.warning(f"Attempted to delete movie ID {movie_id}, but no matching record found.")
                return False
        except sqlite3.Error as e:
            logging.exception(f"Database error deleting movie ID {movie_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        """Deletes a specific user and relies on ON DELETE CASCADE for associated movies."""
        # ... (no changes needed) ...
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"Deleted user ID: {user_id} (associated movies should cascade if constraint is active)")
                return True
            else:
                 logging.warning(f"Attempted to delete user ID {user_id}, but no matching record found.")
                 return False
        except sqlite3.Error as e:
            logging.exception(f"Database error deleting user ID {user_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()