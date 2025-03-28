from flask import Flask, render_template, request, redirect, url_for, flash
from data_manager.sqlite_data_manager import SQLiteDataManager
from urllib.parse import urlparse
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for flash messages
data_manager = SQLiteDataManager('movies.db')

# --- Helper Functions ---
def is_valid_image_url(url):
    """Check if a URL is a valid and accessible image URL."""
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            response = requests.head(url)
            return response.status_code == 200 and response.headers['content-type'].startswith('image')
        else:
            return False
    except:
        return False

# --- Routes ---

@app.route('/')
def home():
    """Home page."""
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    """Lists favorite movies for a specific user."""
    user = data_manager.get_user_by_id(user_id)
    movies = data_manager.get_movies_for_user(user_id)
    if user:
        return render_template('user_movies.html', user=user, movies=movies)
    else:
        flash("User not found.")
        return redirect(url_for('home'))

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Adds a new user."""
    if request.method == 'POST':
        username = request.form['username']
        data_manager.add_user(username)
        return redirect(url_for('home'))
    else:
        return render_template('add_user.html')

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Deletes a user."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for('home'))

    data_manager.delete_user(user_id)
    return redirect(url_for('home'))

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """Adds a new movie to a user's list."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        plot = request.form.get('plot', '').strip()
        poster = request.form.get('poster', '').strip()
        rating = request.form.get('rating', '')

        # --- Data Validation ---
        if not title or not director:
            flash("Title and Director are required.")
            return render_template('add_movie.html', user=user)

        if poster and not is_valid_image_url(poster):
            flash("Invalid poster URL.")
            return render_template('add_movie.html', user=user)

        try:
            rating = float(rating) if rating else None  # Allow empty rating
            if rating is not None and (rating < 0.0 or rating > 10.0):
                flash("Rating must be between 0.0 and 10.0.")
                return render_template('add_movie.html', user=user)
        except ValueError:
            flash("Invalid rating format.  Must be a number.")
            return render_template('add_movie.html', user=user)

        result = data_manager.add_movie(user_id, title, director, plot, poster, rating)

        if result:
            flash(f"Successfully added movie: {title}")
        else:
            flash(f"Failed to add movie: {title}")

        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('add_movie.html', user=user)


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """Updates details of a specific movie."""
    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_movie_by_id(movie_id)

    if not user or not movie:
        flash("User or Movie not found.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        plot = request.form.get('plot', '').strip()
        poster = request.form.get('poster', '').strip()
        rating = request.form.get('rating', '')

        # --- Data Validation ---
        if not title or not director:
            flash("Title and Director are required.")
            return render_template('update_movie.html', user=user, movie=movie)

        if poster and not is_valid_image_url(poster):
            flash("Invalid poster URL.")
            return render_template('update_movie.html', user=user, movie=movie)

        try:
            rating = float(rating) if rating else None  # Allow empty rating
            if rating is not None and (rating < 0.0 or rating > 10.0):
                flash("Rating must be between 0.0 and 10.0.")
                return render_template('update_movie.html', user=user, movie=movie)
        except ValueError:
            flash("Invalid rating format.  Must be a number.")
            return render_template('update_movie.html', user=user, movie=movie)

        if data_manager.update_movie(movie_id, title, director, plot, poster, rating):
            flash("Movie updated successfully.")
        else:
            flash("Failed to update movie.")
        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('update_movie.html', user=user, movie=movie)


@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>')
def delete_movie(user_id, movie_id):
    """Deletes a specific movie from a user's list."""
    data_manager.delete_movie(movie_id)
    return redirect(url_for('user_movies', user_id=user_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)