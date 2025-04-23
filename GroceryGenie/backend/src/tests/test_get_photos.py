import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_get_uploaded_photos(client):
    response = client.get('/get-uploaded-photos', follow_redirects=True)
    assert response.status_code == 200
    assert b'http' in response.data or b'photos' in response.data