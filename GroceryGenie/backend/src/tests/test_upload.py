import sys
import os
import io
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_image_upload(client):
    # Simulate a real image with basic JPEG header
    fake_image = io.BytesIO()
    fake_image.write(b'\xff\xd8\xff\xe0' + b'0' * 100)  # JPEG header
    fake_image.seek(0)

    data = {
        'file': (fake_image, 'banana.jpg')
    }

    response = client.post('/upload', content_type='multipart/form-data', data=data, follow_redirects=True)

    assert response.status_code == 200
    assert b'item' in response.data or b'success' in response.data or b'inventory' in response.data
    