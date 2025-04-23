import sys
import os
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_register_success(client):
    # Unique email to avoid duplication issue
    unique_email = f"pytest_{int(time.time())}@xyz.com"
    response = client.post('/register', data={
        'email': unique_email,
        'password': 'Pytest123!',
        'confirm_pass': 'Pytest123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Welcome' in response.data or b'Logout' in response.data

def test_register_duplicate_email(client):
    # Register a user
    response = client.post('/register', data={
        'email': 'pytest_duplicate@xyz.com',
        'password': 'Pytest123!',
        'confirm_pass': 'Pytest123!'
    }, follow_redirects=True)
    # Try to register again with same email
    response = client.post('/register', data={
        'email': 'pytest_duplicate@xyz.com',
        'password': 'Pytest123!',
        'confirm_pass': 'Pytest123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register' in response.data or b'Already have an account' in response.data

def test_register_missing_password(client):
    response = client.post('/register', data={
        'email': 'pytest_missing@xyz.com',
        'password': '',
        'confirm_pass': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Register' in response.data or b'Password' in response.data