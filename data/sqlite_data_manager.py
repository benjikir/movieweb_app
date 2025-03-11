from abc import ABC, abstractmethod
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Table, Column



class DataManagerInterface(ABC):

    @abstractmethod
    def get_all_users(self):
        pass

    @abstractmethod
    def get_user_movies(self, user_id):
        pass

    @abstractmethod
    def add_user(self, user):
        pass

    @abstractmethod
    def add_movie(self, movie):
        pass

    @abstractmethod
    def update_movie(self, movie):
        pass

    @abstractmethod
    def delete_movie(self, movie_id):
        pass


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db_file_name):
        self.db_file_name = db_file_name  # Store the filename
        self.app = Flask(__name__)  # Need a Flask app for SQLAlchemy
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_name}'
        self.db = SQLAlchemy(self.app)

        # Define the User and Movie models (assuming a simple schema)
        class User(self.db.Model):
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
            movies = relationship("Movie", secondary="user_movies", back_populates="users")
            # Add other user-related fields as needed

            def __repr__(self):
                return f'<User {self.username}>'

        class Movie(self.db.Model):
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            title: Mapped[str] = mapped_column(String(120), nullable=False)
            users = relationship("User", secondary="user_movies", back_populates="movies")
            # Add other movie-related fields as needed

            def __repr__(self):
                return f'<Movie {self.title}>'

        user_movies = Table(
            "user_movies",
            self.db.metadata,
            Column("user_id", ForeignKey("user.id"), primary_key=True),
            Column("movie_id", ForeignKey("movie.id"), primary_key=True),
        )

        self.User = User  # Assign the User model to the class
        self.Movie = Movie # Assign the Movie model to the class
        self.user_movies = user_movies

        # Create the tables (only if they don't exist) - Do this *after* defining the models
        with self.app.app_context():
            self.db.create_all()


    def get_all_users(self):
        with self.app.app_context():
            users = self.User.query.all()
            return [user.id for user in users]


    def get_user_movies(self, user_id):
        with self.app.app_context():
            user = self.User.query.get(user_id)
            if user:
                return [movie.id for movie in user.movies]
            else:
                return []

    def add_user(self, username):
        with self.app.app_context():
            try:
                new_user = self.User(username=username)
                self.db.session.add(new_user)
                self.db.session.commit()
                return new_user.id  # Return the ID of the newly added user
            except Exception as e:
                self.db.session.rollback()
                print(f"Error adding user: {e}")
                return None  # Indicate failure

    def add_movie(self, title):
        with self.app.app_context():
            try:
                new_movie = self.Movie(title=title)
                self.db.session.add(new_movie)
                self.db.session.commit()
                return new_movie.id  # Return the ID of the newly added movie
            except Exception as e:
                self.db.session.rollback()
                print(f"Error adding movie: {e}")
                return None # Indicate failure

    def update_movie(self, movie_id, new_title):
        with self.app.app_context():
            try:
                movie = self.Movie.query.get(movie_id)
                if movie:
                    movie.title = new_title
                    self.db.session.commit()
                    return True # Indicate success
                else:
                    return False # Movie not found
            except Exception as e:
                self.db.session.rollback()
                print(f"Error updating movie: {e}")
                return False # Indicate failure

    def delete_movie(self, movie_id):
        with self.app.app_context():
            try:
                movie = self.Movie.query.get(movie_id)
                if movie:
                    self.db.session.delete(movie)
                    self.db.session.commit()
                    return True # Indicate success
                else:
                    return False # Movie not found
            except Exception as e:
                self.db.session.rollback()
                print(f"Error deleting movie: {e}")
                return False  # Indicate failure


# Example Usage (after defining SQLiteDataManager)
if __name__ == '__main__':
    #from flask import Flask
    # Replace 'test.db' with your desired database file name
    db_file = 'test.db'
    data_manager = SQLiteDataManager(db_file)

    # Example: Create some users (only do this once, or it will error)
    with data_manager.app.app_context():
        # Example: Add some users (only do this once, or it will error)
        existing_user = data_manager.User.query.filter_by(username='john_doe').first()
        if not existing_user:
            new_user = data_manager.User(username='john_doe')
            data_manager.db.session.add(new_user)
            data_manager.db.session.commit()

        existing_movie = data_manager.Movie.query.filter_by(title='Movie1').first()
        if not existing_movie:
            new_movie = data_manager.Movie(title='Movie1')
            data_manager.db.session.add(new_movie)

        existing_movie = data_manager.Movie.query.filter_by(title='Movie2').first()
        if not existing_movie:
            new_movie = data_manager.Movie(title='Movie2')
            data_manager.db.session.add(new_movie)

        existing_movie = data_manager.Movie.query.filter_by(title='Movie3').first()
        if not existing_movie:
            new_movie = data_manager.Movie(title='Movie3')
            data_manager.db.session.add(new_movie)
        data_manager.db.session.commit()


