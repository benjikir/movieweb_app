from flask import Flask, render_template, request, redirect, url_for
from data_manager.sqlite_data_manager import SQLiteDataManager

app = Flask(__name__)
data_manager = SQLiteDataManager('movies.db')

# --- Routes ---

@app.route('/')
def home():
    """Home page."""
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
        return redirect(url_for('home'))  # Redirect to the users list
    else:
        return render_template('add_user.html')  # Create an add_user.html form

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Deletes a user."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        return "User not found", 404

    # Delete the user
    data_manager.delete_user(user_id)  # Add this to your SQLiteDataManager class
    return redirect(url_for('home'))  # Redirect to the users list

@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """Adds a new movie to a user's list."""
    user = data_manager.get_user_by_id(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        plot = request.form.get('plot', '').strip()
        poster = request.form.get('poster', '').strip()

        print(f"Received data: Title={title}, Director={director}, Plot={plot}, Poster={poster}")  # Debugging

        if not title or not director:
            return "Title and Director are required", 400

        result = data_manager.add_movie(user_id, title, director, plot, poster)

        if result:
            print(f"Successfully added movie: {title}")
        else:
            print(f"Failed to add movie: {title}")

        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('add_movie.html', user=user)


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """Updates details of a specific movie."""
    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_movie_by_id(movie_id)
    if not user or not movie:
        return "User or Movie not found", 404

    if request.method == 'POST':
        # Retrieve updated values from the form
        title = request.form['title']
        director = request.form['director']
        plot = request.form.get('plot', '')  # Get plot, default to empty string if not provided
        poster = request.form.get('poster', '')  # Get poster URL, default to empty if not provided
        rating = request.form.get('rating', '')  # Get rating, default to empty if not provided

        # Update the movie with the new values
        data_manager.update_movie(movie_id, title, director, plot, poster, rating)

        # Redirect to the movie list for the user
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