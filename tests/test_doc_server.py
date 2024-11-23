"""Unit tests for the documentation server."""

import os
import pytest
import json
from pathlib import Path
from doc_server import app, get_documentation_files, read_markdown_file

@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_docs(tmp_path):
    """Create a temporary documentation directory."""
    doc_path = tmp_path / 'documentation'
    doc_path.mkdir()
    
    # Create test files
    (doc_path / 'test1.md').write_text('# Test 1\nContent 1')
    (doc_path / 'test2.md').write_text('# Test 2\nContent 2')
    return doc_path

def test_get_documentation_files(test_docs):
    """Test documentation file listing"""
    files = get_documentation_files(test_docs)
    
    assert len(files) == 2
    file_names = [f['name'] for f in files]
    assert 'test1.md' in file_names
    assert 'test2.md' in file_names

def test_read_markdown_file(test_docs):
    """Test markdown file reading"""
    content = read_markdown_file(test_docs, 'test1.md')
    assert '<h1 id="test-1">Test 1</h1>' in content
    assert '<p>Content 1</p>' in content

def test_index_route(client):
    """Test the index route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Documentation Viewer' in response.data

def test_api_docs_route(client, test_docs, monkeypatch):
    """Test the API docs listing route"""
    monkeypatch.setattr('doc_server.doc_base_path', test_docs)
    
    response = client.get('/api/docs')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 2
    file_names = [f['name'] for f in data]
    assert 'test1.md' in file_names
    assert 'test2.md' in file_names

def test_api_doc_route(client, test_docs, monkeypatch):
    """Test the API doc content route"""
    monkeypatch.setattr('doc_server.doc_base_path', test_docs)
    
    # Test valid file
    response = client.get('/api/doc/test1.md')
    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert '<h1 id="test-1">Test 1</h1>' in data['content']
    assert '<p>Content 1</p>' in data['content']
    
    # Test invalid file
    response = client.get('/api/doc/nonexistent.md')
    assert response.status_code == 404

def test_static_route(client):
    """Test the static file route"""
    response = client.get('/static/js/main.js')
    assert response.status_code == 200
