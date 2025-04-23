import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_login_success(client):
    # First register a user
    client.post('/register', data={
        'email': 'loginuser@xyz.com',
        'password': 'Login123!',
        'confirm_pass': 'Login123!'
    }, follow_redirects=True)

    # Now login
    response = client.post('/login', data={
        'email': 'loginuser@xyz.com',
        'password': 'Login123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Logout' in response.data

def test_login_wrong_password(client):
    # Assuming user is already registered above
    response = client.post('/login', data={
        'email': 'loginuser@xyz.com',
        'password': 'WrongPass!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid credentials' in response.data or b'Login' in response.data

def test_login_unregistered_user(client):
    response = client.post('/login', data={
        'email': 'nouser@xyz.com',
        'password': 'SomePass123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid credentials' in response.data or b'Login' in response.data