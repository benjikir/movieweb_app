import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from data_manager.sqlite_data_manager import SQLiteDataManager, OMDbException
from urllib.parse import urlparse
from datetime import datetime # Import datetime for year validation

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_very_secure_default_secret_key_for_dev")
data_manager = SQLiteDataManager('movies.db')
logging.basicConfig(level=logging.INFO)

# --- Helper Functions ---
def is_valid_url_format(url):
    # ... (no changes) ...
    if not url: return True
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

def parse_year(year_str):
    """Safely parses a year string into an integer, returns None if invalid."""
    if not year_str:
        return None
    try:
        # Handle potential ranges like '2009–2011' -> take first year
        first_part = year_str.split('–')[0].split('-')[0].strip()
        year = int(first_part)
        # Add a basic sanity check for year range
        current_year = datetime.now().year
        if 1880 <= year <= current_year + 5: # Allow a bit into the future
             return year
        else:
             logging.warning(f"Year {year} out of reasonable range (1880-{current_year+5}).")
             return None
    except (ValueError, TypeError):
        logging.warning(f"Could not parse year string: '{year_str}'")
        return None

# --- Routes ---

@app.route('/')
def home():
    # ... (no changes) ...
    return render_template('home.html')

@app.route('/users')
def list_users():
     # ... (no changes) ...
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
def user_movies(user_id):
     # ... (no changes) ...
    user = data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for('list_users'))
    movies = data_manager.get_movies_for_user(user_id)
    return render_template('user_movies.html', user=user, movies=movies)

# --- User Management Routes ---

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    # ... (no changes) ...
    add_user_template = 'add_user.html'
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash("Username cannot be empty.", "warning")
            return render_template(add_user_template)
        result = data_manager.add_user(username)
        if result == True:
             flash(f"User '{username}' added successfully.", "success")
             return redirect(url_for('list_users'))
        elif result == False:
            flash(f"Username '{username}' already exists.", "danger")
            return render_template(add_user_template, form_data=request.form)
        else:
             flash(f"Database error adding user '{username}'. Check logs.", "danger")
             return render_template(add_user_template, form_data=request.form)
    return render_template(add_user_template, form_data={})

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    # ... (no changes) ...
    user = data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for('list_users'))
    if data_manager.delete_user(user_id):
        flash(f"User '{user['username']}' and their movies deleted successfully.", "success")
    else:
        flash(f"Failed to delete user '{user['username']}'. Check logs.", "danger")
    return redirect(url_for('list_users'))

# --- Movie Management Routes ---

# --- MODIFIED add_movie to handle year ---
@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    user = data_manager.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for('list_users'))

    add_movie_template = 'add_movie.html'

    if request.method == 'POST':
        app.logger.info(f"Add movie form data: {request.form}")
        add_method = request.form.get('add_method')
        title = request.form.get('title', '').strip()
        year_int = None # Initialize year

        if not title:
            flash("Movie Title is always required.", "warning")
            return render_template(add_movie_template, user=user, form_data=request.form)

        if add_method == 'fetch':
            try:
                movie_data = data_manager.fetch_movie_details_from_omdb(title)
                fetched_title = movie_data.get('Title', title)
                director = movie_data.get('Director', 'N/A')
                year_str = movie_data.get('Year') # Get year string from API
                year_int = parse_year(year_str) # Use helper function to parse
                plot = movie_data.get('Plot', '')
                poster = movie_data.get('Poster')
                if poster == 'N/A': poster = ''
                rating_str = movie_data.get('imdbRating', None)
                rating = None
                if rating_str and rating_str.lower() != 'n/a':
                    try:
                        rating = float(rating_str)
                    except ValueError:
                        rating = None

                # Pass year_int to data_manager
                if data_manager.add_movie(user_id, fetched_title, director, year_int, plot, poster, rating):
                     flash(f"Successfully fetched and added movie: {fetched_title}", "success")
                     return redirect(url_for('user_movies', user_id=user_id))
                else:
                     flash(f"Database error saving fetched movie data.", "danger")
                     return render_template(add_movie_template, user=user, form_data=request.form)

            except OMDbException as e:
                flash(f"OMDb API Error: {e}", "danger")
                return render_template(add_movie_template, user=user, form_data=request.form)
            except Exception as e:
                flash(f"An unexpected error occurred fetching data: {e}", "danger")
                app.logger.error(f"Error fetching OMDb data for title '{title}': {e}", exc_info=True)
                return render_template(add_movie_template, user=user, form_data=request.form)

        elif add_method == 'manual':
            director = request.form.get('director', '').strip()
            year_str = request.form.get('year', '').strip() # Get year from form
            plot = request.form.get('plot', '').strip()
            poster = request.form.get('poster', '').strip()
            rating_str = request.form.get('rating', '').strip()
            rating = None

            # Validation for manual entry
            if not director:
                flash("Director is required for manual entry.", "warning")
                return render_template(add_movie_template, user=user, form_data=request.form)

            # Validate year (optional, but good)
            year_int = parse_year(year_str)
            if year_str and year_int is None: # Check if year was entered but invalid
                 flash("Invalid year format or out of range.", "warning")
                 return render_template(add_movie_template, user=user, form_data=request.form)
            # Note: Year is optional, so year_int can be None if year_str is empty

            if poster and not is_valid_url_format(poster):
                flash("Invalid Poster URL format.", "warning")
                return render_template(add_movie_template, user=user, form_data=request.form)

            if rating_str:
                try:
                    rating = float(rating_str)
                    if not (0.0 <= rating <= 10.0):
                        flash("Rating must be between 0.0 and 10.0.", "warning")
                        return render_template(add_movie_template, user=user, form_data=request.form)
                except ValueError:
                    flash("Invalid rating format.", "warning")
                    return render_template(add_movie_template, user=user, form_data=request.form)

            # Pass year_int to data_manager
            if data_manager.add_movie(user_id, title, director, year_int, plot, poster, rating):
                flash(f"Successfully added movie manually: {title}", "success")
                return redirect(url_for('user_movies', user_id=user_id))
            else:
                flash(f"Database error adding movie manually.", "danger")
                return render_template(add_movie_template, user=user, form_data=request.form)
        else:
            flash("Invalid add method selected.", "warning")
            return render_template(add_movie_template, user=user, form_data=request.form)

    # GET request
    return render_template(add_movie_template, user=user, form_data={})

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    # ... (no changes needed here, year is fetched from DB) ...
    movie = data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "warning")
        return redirect(url_for('list_users'))
    user = data_manager.get_user_by_id(movie['user_id'])
    if not user:
         app.logger.error(f"Data inconsistency: Movie ID {movie_id}, User ID {movie['user_id']} not found.")
         flash("Could not find the user associated with this movie.", "danger")
         return redirect(url_for('list_users'))
    return render_template('movie_detail.html', movie=movie, user=user)

# --- MODIFIED update_movie to handle year ---
@app.route('/movie/<int:movie_id>/update', methods=['GET', 'POST'])
def update_movie(movie_id):
    original_movie = data_manager.get_movie_by_id(movie_id)
    if not original_movie:
        flash("Movie not found.", "warning")
        return redirect(url_for('list_users'))

    user = data_manager.get_user_by_id(original_movie['user_id'])
    if not user:
         app.logger.error(f"Data inconsistency: Movie ID {movie_id}, User ID {original_movie['user_id']} not found during update.")
         flash("Could not find the user associated with this movie.", "danger")
         return redirect(url_for('list_users'))

    update_template = 'update_movie.html'

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        director = request.form.get('director', '').strip()
        year_str = request.form.get('year', '').strip() # Get year from form
        plot = request.form.get('plot', '').strip()
        poster = request.form.get('poster', '').strip()
        rating_str = request.form.get('rating', '').strip()
        rating = None

        # Validation
        if not title or not director:
            flash("Title and Director are required.", "warning")
            return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)

        # Validate year
        year_int = parse_year(year_str)
        if year_str and year_int is None: # Check if year was entered but invalid
             flash("Invalid year format or out of range.", "warning")
             return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)

        if poster and not is_valid_url_format(poster):
            flash("Invalid Poster URL format.", "warning")
            return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)

        if rating_str:
            try:
                rating = float(rating_str)
                if not (0.0 <= rating <= 10.0):
                    flash("Rating must be between 0.0 and 10.0.", "warning")
                    return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)
            except ValueError:
                flash("Invalid rating format.", "warning")
                return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)

        # Pass year_int to data_manager update
        if data_manager.update_movie(movie_id, title, director, year_int, plot, poster, rating):
            flash(f"Movie '{title}' updated successfully.", "success")
            return redirect(url_for('movie_detail', movie_id=movie_id))
        else:
            flash(f"Database error updating movie '{title}'. Check logs.", "danger")
            return render_template(update_template, user=user, movie=request.form, movie_id=movie_id)

    # GET request
    return render_template(update_template, user=user, movie=original_movie, movie_id=movie_id)

@app.route('/movie/<int:movie_id>/delete', methods=['POST'])
def delete_movie(movie_id):
    # ... (no changes needed here) ...
    movie = data_manager.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found.", "warning")
        return redirect(url_for('list_users'))
    user_id = movie['user_id']
    if data_manager.delete_movie(movie_id):
        flash(f"Movie '{movie['title']}' deleted successfully.", "success")
    else:
        flash(f"Failed to delete movie '{movie['title']}'. Check logs.", "danger")
    return redirect(url_for('user_movies', user_id=user_id))

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    # ... (no changes) ...
    app.logger.warning(f"404 Not Found error: {request.url} - {e}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # ... (no changes) ...
    app.logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)