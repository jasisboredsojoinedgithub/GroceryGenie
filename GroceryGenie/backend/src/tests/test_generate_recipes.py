import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_generate_recipes(client):
    # Simulate data that would come from inventory
    data = {
        'ingredients': 'banana,tomato,bread'
    }
    response = client.post('/generate-recipes', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'recipe' in response.data or b'suggestion' in response.data