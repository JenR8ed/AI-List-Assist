import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Setup environment before importing app
os.environ.setdefault('SECRET_KEY', 'smoke-test-secret')
os.environ.setdefault('API_KEY', 'smoke-test-api-key')
os.environ.setdefault('EBAY_CLIENT_ID', 'smoke-test-client-id')
os.environ.setdefault('EBAY_CLIENT_SECRET', 'smoke-test-client-secret')
os.environ.setdefault('GEMINI_API_KEY', 'smoke-test-gemini-key')
os.environ.setdefault('PERPLEXITY_API_KEY', 'smoke-test-perplexity-key')
os.environ.setdefault('GOOGLE_API_KEY', 'smoke-test-google-key')

from app_enhanced import app, init_db
from shared.models import ConversationState

@pytest.fixture(autouse=True)
def setup_teardown():
    with app.app_context():
        init_db()
    yield
    for db_file in ('listings.db', 'valuations.db', 'consignment.db'):
        try:
            os.remove(db_file)
        except OSError:
            pass
    import shutil
    try:
        shutil.rmtree('test_uploads')
    except OSError:
        pass

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Ensure UPLOAD_FOLDER exists
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    os.makedirs('test_uploads', exist_ok=True)
    with app.test_client() as c:
        yield c

def test_create_listing_no_data(client):
    response = client.post('/api/listing/create', headers={'Authorization': 'Bearer smoke-test-api-key'}, json={})
    assert response.status_code == 400
    assert response.json == {"error": "No JSON data provided"}

def test_create_listing_missing_fields(client):
    response = client.post('/api/listing/create', headers={'Authorization': 'Bearer smoke-test-api-key'}, json={'item_id': '123'})
    assert response.status_code == 400
    assert response.json == {"error": "item_id and session_id required"}

def test_create_listing_session_not_found(client):
    with patch('app_enhanced.conversation_orchestrator.get_state', return_value=None):
        response = client.post('/api/listing/create', headers={'Authorization': 'Bearer smoke-test-api-key'}, json={'item_id': '123', 'session_id': '456'})
        assert response.status_code == 404
        assert response.json == {"error": "Conversation session not found"}

@patch('services.conversation_orchestrator.ConversationOrchestrator.get_state')
@patch('services.listing_synthesis.ListingSynthesisEngine.create_listing_draft')
@patch('services.draft_image_manager.DraftImageManager.save_draft_images')
def test_create_listing_success(mock_save_images, mock_create_draft, mock_get_state, client):
    # Initialize global listing_engine
    import app_enhanced
    from services.listing_synthesis import ListingSynthesisEngine
    app_enhanced.listing_engine = ListingSynthesisEngine()

    # Mock conversation state
    item_id = "test_item"
    session_id = "test_session"
    listing_id = "test_listing"

    mock_state = ConversationState(session_id=session_id, item_id=item_id)
    mock_state.known_fields = {"item_name": "Test Name", "price": 10.0}
    mock_get_state.return_value = mock_state

    # Mock listing draft
    from shared.models import ListingDraft, ItemCondition
    from datetime import datetime

    mock_draft = ListingDraft(
        listing_id=listing_id,
        item_id=item_id,
        title="Test Title",
        description="Test Description",
        category_id="123",
        condition=ItemCondition.USED,
        price=10.0,
        created_at=datetime.now()
    )
    mock_create_draft.return_value = mock_draft

    # Mock save images
    mock_save_images.return_value = ["test_image.jpg"]

    # Insert dummy session data for images to trigger image path logic
    import sqlite3
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, session_data TEXT, created_at DATETIME)')
    c.execute('INSERT INTO sessions (session_id, session_data) VALUES (?, ?)', (session_id, '{"image_filename": "test.jpg"}'))
    conn.commit()
    conn.close()

    response = client.post('/api/listing/create', headers={'Authorization': 'Bearer smoke-test-api-key'}, json={'item_id': item_id, 'session_id': session_id})

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["listing"]["listing_id"] == listing_id
    assert response.json["listing"]["title"] == "Test Title"

    # Verify DB insertion
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()
    c.execute('SELECT listing_id, item_id, title, status FROM listings WHERE listing_id = ?', (listing_id,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == listing_id
    assert row[1] == item_id
    assert row[2] == "Test Title"
    assert row[3] == "draft"

@patch('services.conversation_orchestrator.ConversationOrchestrator.get_state')
def test_create_listing_internal_error(mock_get_state, client):
    # Mock get_state to throw an exception to trigger 500 error
    mock_get_state.side_effect = Exception("Test Error")

    response = client.post('/api/listing/create', headers={'Authorization': 'Bearer smoke-test-api-key'}, json={'item_id': '123', 'session_id': '456'})

    assert response.status_code == 500
    assert response.json == {"error": "An internal server error occurred."}
