import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import tempfile
import pytest
from app import app, db, User, Restaurant, Reservation
@pytest.fixture()
def client():
    app.config["TESTING"] = True
    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield client

def register(client, username, password):
    return client.post('/register', data={'username': username, 'password': password}, follow_redirects=True)

def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def test_register_login(client):
    rv = register(client, "user1", "pass")
    assert b"Logout" in rv.data

    rv = login(client, "user1", "pass")
    assert b"Logout" in rv.data

def test_post_restaurant_and_reserve(client):
    register(client, 'user2', 'pass')
    login(client, 'user2', 'pass')

    rv = client.post('/restaurants', data={'name': 'Test R', 'description': 'Desc'}, follow_redirects=True)
    assert b'Test R' in rv.data

    with app.app_context():
        restaurant = Restaurant.query.filter_by(name='Test R').first()
    assert restaurant is not None

    rv = client.post(f'/restaurants/{restaurant.id}/reserve', data={'time': '2030-01-01 18:00'}, follow_redirects=True)
    assert b'My Reservations' in rv.data
