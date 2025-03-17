import pytest
from app import app
from data_manager.sqlite_data_manager import SQLiteDataManager
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from flask import render_template

@app.route('/users')
def users_page():
    return render_template("users.html")


data_manager = SQLiteDataManager('test_movies.db')
# Use a mock or a test database for SQLiteDataManager



@pytest.fixture(scope='module')
def test_client():
    # Set the app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use an in-memory database for testing
    with app.test_client() as client:
        # Setup the application context
        with app.app_context():
            # Optionally, initialize your test database here
            pass
        yield client



@pytest.fixture
def create_movie(create_user):
    """Fixture to create a movie for a specific user."""
    with app.app_context():
        # Create a movie for the created user
        movie = data_manager.add_movie(create_user['id'], 'Test Movie', 'Director', 'Plot', 'Poster')
        return movie


def test_home(test_client):
    """Test the home route."""
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Users" in response.data  # Check if the response contains 'Users' (adjust based on actual HTML)


def test_add_user(test_client):
    """Test adding a new user."""
    response = test_client.post('/add_user', data={'username': 'newuser'})
    assert response.status_code == 302  # Expecting a redirect after adding a user
    assert response.location in ("/", "http://localhost/")



def test_user_not_found(test_client):
    """Test the 404 error handler for a non-existing user."""
    response = test_client.get('/users/99999')  # Non-existing user ID
    assert response.status_code == 404
    assert b"User not found" in response.data


def test_page_not_found(test_client):
    """Test the 404 error page."""
    response = test_client.get('/nonexistent_page')
    assert response.status_code == 404
    assert b"<h1>404 - Page Not Found</h1>" in response.data



def test_internal_server_error(test_client):
    with pytest.raises(Exception):
        response = test_client.get('/cause_500')
        assert response.status_code == 500

