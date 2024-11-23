from flask import Flask, render_template, send_from_directory, jsonify
import markdown
import os
from pathlib import Path
import json
import argparse

app = Flask(__name__)

# Global variable to store documentation path
doc_base_path = None

def get_documentation_files(doc_dir):
    """Get list of documentation files with their directories"""
    files = []
    for root, _, filenames in os.walk(doc_dir):
        rel_path = os.path.relpath(root, doc_dir)
        if rel_path == '.':
            rel_path = ''
        
        for filename in filenames:
            if filename.endswith('.md'):
                directory = rel_path if rel_path != '.' else ''
                files.append({
                    'name': os.path.splitext(filename)[0],
                    'directory': directory,
                    'path': os.path.join(rel_path, filename)
                })
    return files

def read_markdown_file(doc_dir, file_path):
    """Read and convert markdown file to HTML."""
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
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/docs')
def get_docs():
    """Get list of documentation files."""
    files = get_documentation_files(doc_base_path)
    return jsonify(files)

@app.route('/api/doc/<path:file_path>')
def get_doc(file_path):
    """Get content of a specific documentation file."""
    html_content = read_markdown_file(doc_base_path, file_path)
    return jsonify({'content': html_content})

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

def start_server(port=5000, local=False):
    """Start the documentation server."""
    global doc_base_path
    if local:
        doc_base_path = os.path.join(os.getcwd(), 'documentation')
    else:
        doc_base_path = os.path.join(os.getcwd(), 'cloned_repo', 'documentation')
    
    print(f"Starting documentation server at http://localhost:{port}")
    print(f"Serving documentation from: {doc_base_path}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the documentation server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--local', action='store_true', help='Use local documentation folder instead of cloned_repo')
    args = parser.parse_args()
    
    start_server(port=args.port, local=args.local)
