import os
import pytest
from pathlib import Path
from doc_server import app, get_documentation_files, read_markdown_file

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_docs(tmp_path):
    """Create test documentation files"""
    doc_dir = tmp_path / 'documentation'
    doc_dir.mkdir()
    
    # Create test files
    (doc_dir / 'test1.md').write_text('# Test 1\nContent 1')
    
    subdir = doc_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'test2.md').write_text('# Test 2\nContent 2')
    
    return doc_dir

def test_get_documentation_files(test_docs):
    """Test documentation file listing"""
    files = get_documentation_files(test_docs)
    
    assert len(files) == 2
    assert any(f['name'] == 'test1' and f['directory'] == '/' for f in files)
    assert any(f['name'] == 'test2' and f['directory'] == '/subdir' for f in files)

def test_read_markdown_file(test_docs):
    """Test markdown file reading and conversion"""
    # Test valid file
    content = read_markdown_file(test_docs, 'test1.md')
    assert '<h1 id="test-1">Test 1</h1>' in content
    assert '<p>Content 1</p>' in content
    
    # Test file in subdirectory
    content = read_markdown_file(test_docs, 'subdir/test2.md')
    assert '<h1 id="test-2">Test 2</h1>' in content
    assert '<p>Content 2</p>' in content
    
    # Test nonexistent file
    content = read_markdown_file(test_docs, 'nonexistent.md')
    assert 'Error reading file' in content

def test_index_route(client):
    """Test the index route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Documentation Viewer' in response.data

def test_api_docs_route(client, test_docs, monkeypatch):
    """Test the API docs listing route"""
    # Mock the current working directory and create documentation directory
    repo_path = test_docs.parent / 'cloned_repo'
    repo_path.mkdir()
    doc_path = repo_path / 'documentation'
    doc_path.mkdir()
    
    # Create test files
    (doc_path / 'test1.md').write_text('# Test 1\nContent 1')
    (doc_path / 'subdir').mkdir()
    (doc_path / 'subdir' / 'test2.md').write_text('# Test 2\nContent 2')
    
    monkeypatch.setattr(os, 'getcwd', lambda: str(test_docs.parent))
    
    response = client.get('/api/docs')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data) == 2
    assert any(f['name'] == 'test1' for f in data)
    assert any(f['name'] == 'test2' for f in data)

def test_api_doc_route(client, test_docs, monkeypatch):
    """Test the API doc content route"""
    # Mock the current working directory and create documentation directory
    repo_path = test_docs.parent / 'cloned_repo'
    repo_path.mkdir()
    doc_path = repo_path / 'documentation'
    doc_path.mkdir()
    
    # Create test file
    (doc_path / 'test1.md').write_text('# Test 1\nContent 1')
    
    monkeypatch.setattr(os, 'getcwd', lambda: str(test_docs.parent))
    
    # Test valid file
    response = client.get('/api/doc/test1.md')
    assert response.status_code == 200
    data = response.get_json()
    assert '<h1 id="test-1">Test 1</h1>' in data['content']
    
    # Test nonexistent file
    response = client.get('/api/doc/nonexistent.md')
    assert response.status_code == 200
    data = response.get_json()
    assert 'Error reading file' in data['content']

def test_static_route(client):
    """Test static file serving"""
    # This test assumes you have static files in your static directory
    response = client.get('/static/css/style.css')
    assert response.status_code == 200
    assert b'background-color' in response.data
