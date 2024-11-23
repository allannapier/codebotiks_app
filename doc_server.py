"""Flask web server for viewing repository documentation."""

import os
from pathlib import Path
from typing import List, Dict, Any, Union
import markdown
import json
from flask import Flask, render_template, send_from_directory, jsonify

app = Flask(__name__)

def get_documentation_files(doc_dir: Union[str, Path]) -> List[Dict[str, str]]:
    """Get list of documentation files with their directories.
    
    Args:
        doc_dir: Documentation directory path.
        
    Returns:
        List of dictionaries containing file information:
        - name: File name without extension
        - directory: Directory path relative to doc_dir
        - path: Full relative path from doc_dir
    """
    files = []
    for root, _, filenames in os.walk(doc_dir):
        rel_path = os.path.relpath(root, doc_dir)
        if rel_path == '.':
            rel_path = ''
        for filename in filenames:
            if filename.endswith('.md'):
                name = os.path.splitext(filename)[0]
                directory = '/' + rel_path if rel_path else '/'
                files.append({
                    'name': name,
                    'directory': directory,
                    'path': os.path.join(rel_path, filename)
                })
    return files

def read_markdown_file(doc_dir: Union[str, Path], file_path: str) -> str:
    """Read and convert markdown file to HTML.
    
    Args:
        doc_dir: Documentation directory path.
        file_path: Relative path to markdown file.
        
    Returns:
        HTML content of the markdown file.
    """
    full_path = os.path.join(doc_dir, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Convert markdown to HTML with code highlighting
        html = markdown.markdown(
            content,
            extensions=['fenced_code', 'codehilite', 'tables', 'toc']
        )
        return html
    except Exception as e:
        return f"<p>Error reading file: {str(e)}</p>"

@app.route('/')
def index() -> str:
    """Serve the main page.
    
    Returns:
        Rendered HTML template.
    """
    return render_template('index.html')

@app.route('/api/docs')
def get_docs() -> Any:
    """Get list of documentation files.
    
    Returns:
        JSON response with file information.
    """
    doc_dir = os.path.join(os.getcwd(), 'cloned_repo', 'documentation')
    files = get_documentation_files(doc_dir)
    return jsonify(files)

@app.route('/api/doc/<path:file_path>')
def get_doc(file_path: str) -> Any:
    """Get content of a specific documentation file.
    
    Args:
        file_path: Relative path to markdown file.
        
    Returns:
        JSON response with HTML content.
    """
    doc_dir = os.path.join(os.getcwd(), 'cloned_repo', 'documentation')
    html_content = read_markdown_file(doc_dir, file_path)
    return jsonify({'content': html_content})

@app.route('/static/<path:path>')
def serve_static(path: str) -> Any:
    """Serve static files.
    
    Args:
        path: Static file path.
        
    Returns:
        Static file response.
    """
    return send_from_directory('static', path)

def start_server(port: int = 5000) -> None:
    """Start the documentation server.
    
    Args:
        port: Port number to listen on (default: 5000).
    """
    print(f"Starting documentation server at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    start_server()
