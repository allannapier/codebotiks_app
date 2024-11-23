# Documentation for `doc_server.py`

---

## Flask Documentation Viewer

### Overview

This Flask-based web app provides a user-friendly interface for viewing and navigating repository documentation written in Markdown format.

### Key Components

- **get_documentation_files()**: Retrieves a list of Markdown files within a specified documentation directory and their relative paths.
- **read_markdown_file()**: Converts a Markdown file into HTML format using the `markdown` library for highlighting code and creating a table of contents.
- **index()**: Serves the main HTML page for navigating the documentation.
- **get_docs()**: Returns a JSON response containing a list of Markdown files and their metadata.
- **get_doc()**: Returns the HTML content of a specific Markdown file.
- **serve_static()**: Serves static files like CSS and JavaScript.

### Usage

1. Clone the repository containing the documentation.
2. Run the following command to start the documentation server:
   - `python app.py`

3. Navigate to `http://localhost:5000` in your browser to view the documentation.

### Dependencies and Requirements

- Python 3.6 or later
- Flask
- Markdown
- Jinja2
- MarkupSafe

### Notable Design Decisions

- **Use of Markdown**: Markdown is a lightweight and human-readable format for creating documentation.
- **JSON-based API**: The API endpoints provide a convenient way to access documentation files and content in JSON format.
- **Static file serving**: Static files like CSS and JavaScript are served separately to improve performance.
- **Code highlighting and table of contents**: The `markdown` extension adds syntax highlighting for code blocks and generates a table of contents for easy navigation.

---
*Documentation generated automatically using Google's Gemini AI*