from flask import Flask, render_template, request, redirect, url_for, g
from data_manager.sqlite_data_manager import SQLiteDataManager

app = Flask(__name__)
data_manager = SQLiteDataManager('movies.db')

# --- Routes ---

@app.route('/')
def home():
    """Home page."""
    return render_template('home.html')  # Create a home.html template

@app.route('/users')
def list_users():
    """Lists all users."""
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)  # Create a users.html template

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    """Lists favorite movies for a specific user."""
    user = data_manager.get_user_by_id(user_id)
    movies = data_manager.get_movies_for_user(user_id)
    if user:
        return render_template('user_movies.html', user=user, movies=movies)  # Create user_movies.html
    else:
        return "User not found", 404  # Or redirect to an error page.

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Adds a new user."""
    if request.method == 'POST':
        username = request.form['username']  # Assuming a form field named 'username'
        data_manager.add_user(username)  # You would pass other user details here
        return redirect(url_for('list_users'))  # Redirect to the users list
    else:
        return render_template('add_user.html')  # Create an add_user.html form

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """Adds a new movie to a user's list."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        title = request.form['title']
        director = request.form['director']
        # ... other movie details from the form ...
        data_manager.add_movie(user_id, title, director)  # Pass movie details
        return redirect(url_for('user_movies', user_id=user_id))
    else:
        return render_template('add_movie.html', user=user, user_id=user_id)  # Create add_movie.html

@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """Updates details of a specific movie."""
    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_movie_by_id(movie_id)
    if not user or not movie:
        return "User or Movie not found", 404

    if request.method == 'POST':
        title = request.form['title']
        director = request.form['director']
        # ... other movie details from the form ...
        data_manager.update_movie(movie_id, title, director)
        return redirect(url_for('user_movies', user_id=user_id))
    else:
        # Pass user and movie objects to the template
        return render_template('update_movie.html', user=user, movie=movie)  # Create update_movie.html

@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>')
def delete_movie(user_id, movie_id):
    """Deletes a specific movie from a user's list."""
    data_manager.delete_movie(movie_id)
    return redirect(url_for('user_movies', user_id=user_id))


# Ensure the connection to the database is closed when application shuts down
@app.teardown_appcontext
def close_connection(exception=None):
    """Closes the database connection at the end of each request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    app.run(debug=True)