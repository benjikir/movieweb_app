import sqlite3

class SQLiteDataManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None  # Initialize connection
        self.connect()     # Establish connection during object creation
        self.create_tables()

    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row # Access columns by name
            print(f"Successfully connected to {self.db_file}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            self.conn = None  # Ensure conn is None if connection fails

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def create_tables(self):
        """Create the users and movies tables if they don't exist."""
        if not self.conn:
            print("No database connection.  Cannot create tables.")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    director TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            self.conn.commit()
            print("Tables created or already exist.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def get_all_users(self):
        """Fetch all users from the database."""
        if not self.conn:
            print("No database connection.")
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, username FROM users")
            users = []
            for row in cursor.fetchall():
                user = {'id': row['id'], 'username': row['username']}
                users.append(user)
            return users
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return []

    def get_user_by_id(self, user_id):
        """Fetch a user by their ID."""
        if not self.conn:
            print("No database connection.")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return user
        except sqlite3.Error as e:
            print(f"Error fetching user: {e}")
            return None

    def add_user(self, username):
        """Add a new user to the database."""
        if not self.conn:
            print("No database connection.")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            self.conn.commit()
            print(f"Added user: {username}")
            return True
        except sqlite3.Error as e:
            print(f"Error adding user: {e}")
            return False

    def get_movies_for_user(self, user_id):
        """Fetch all movies for a specific user."""
        if not self.conn:
            print("No database connection.")
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE user_id = ?", (user_id,))
            movies = cursor.fetchall()
            return movies
        except sqlite3.Error as e:
            print(f"Error fetching movies: {e}")
            return []

    def add_movie(self, user_id, title, director):
        """Add a new movie to a user's list."""
        if not self.conn:
            print("No database connection.")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO movies (user_id, title, director) VALUES (?, ?, ?)", (user_id, title, director))
            self.conn.commit()
            print(f"Added movie: {title} for user {user_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error adding movie: {e}")
            return False

    def get_movie_by_id(self, movie_id):
        """Fetch a movie by its ID."""
        if not self.conn:
            print("No database connection.")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
            movie = cursor.fetchone()
            return movie
        except sqlite3.Error as e:
            print(f"Error fetching movie: {e}")
            return None

    def update_movie(self, movie_id, title, director):
        """Update details of a specific movie."""
        if not self.conn:
            print("No database connection.")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE movies SET title = ?, director = ? WHERE id = ?", (title, director, movie_id))
            self.conn.commit()
            print(f"Updated movie {movie_id} to title: {title}, director: {director}")
            return True
        except sqlite3.Error as e:
            print(f"Error updating movie: {e}")
            return False

    def delete_movie(self, movie_id):
        """Delete a specific movie from the database."""
        if not self.conn:
            print("No database connection.")
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            self.conn.commit()
            print(f"Deleted movie: {movie_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error deleting movie: {e}")
            return False