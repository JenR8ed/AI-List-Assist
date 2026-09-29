"""Deterministic fixture intake and SQLite draft creation for local review."""

import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path


FIXTURES = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/local_items.json').read_text())


def intake_fixture(fixture_id: str) -> dict | None:
    fixture = FIXTURES.get(fixture_id)
    if fixture is None:
        return None
    item_id = str(uuid.uuid4())
    item = {'item_id': item_id, 'fixture_id': fixture_id, 'source': 'fixture',
            'name': fixture['name'], 'brand': fixture['brand'],
            'category_id': fixture['category_id'], 'condition': fixture['condition'],
            'notes': fixture['notes'], 'valuation': {'status': 'unavailable', 'source': 'fixture'}}
    with closing(sqlite3.connect('listings.db')) as conn, conn:
        conn.execute('INSERT INTO items (item_id, valuation_json) VALUES (?, ?)',
                     (item_id, json.dumps(item)))
    return item


def get_item(item_id: str) -> dict | None:
    with closing(sqlite3.connect('listings.db')) as conn:
        row = conn.execute('SELECT valuation_json FROM items WHERE item_id = ?', (item_id,)).fetchone()
    return json.loads(row[0]) if row and row[0] else None


def create_fixture_draft(item: dict) -> dict:
    listing_id = str(uuid.uuid4())
    draft = {'listing_id': listing_id, 'item_id': item['item_id'], 'source': 'fixture',
             'title': item['name'], 'description': '', 'category_id': item['category_id'],
             'condition': item['condition'], 'price': None, 'item_specifics': {}, 'images': [],
             'missing_required_specifics': []}
    with closing(sqlite3.connect('listings.db')) as conn, conn:
        conn.execute('INSERT INTO listings (listing_id, item_id, title, price, status, draft_data) '
                     'VALUES (?, ?, ?, ?, ?, ?)',
                     (listing_id, item['item_id'], draft['title'], None, 'draft', json.dumps(draft)))
    return draft
