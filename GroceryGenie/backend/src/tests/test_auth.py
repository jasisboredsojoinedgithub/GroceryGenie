import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.app import app
import pytest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200