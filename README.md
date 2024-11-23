# Repository Documentation Generator

A Python tool that automatically generates documentation for Python files in a GitHub repository using Google's Gemini AI. The tool maintains the repository's directory structure and can optionally create a pull request with the generated documentation.

## Features

- Clones GitHub repositories
- Analyzes Python files using Google's Gemini AI
- Generates detailed documentation including:
  - Code purpose overview
  - Function descriptions
  - Key dependencies
  - Important variables
  - Design patterns
- Maintains repository structure in documentation
- Optional pull request creation with documentation changes

## Prerequisites

1. Python 3.10 or higher
2. Git installed and available in your system's PATH
3. Google Gemini API key
4. GitHub personal access token (if using pull request feature)

## Installation

1. Clone this repository:
```bash
git clone [your-repo-url]
cd [repo-name]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here
```

2. Get your API keys:

### Google Gemini API Key
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key to your `.env` file

### GitHub Personal Access Token (Optional - needed for PR creation)
1. Go to GitHub.com
2. Click your profile picture → Settings
3. Scroll down to Developer settings → Personal access tokens → Tokens (classic)
4. Generate new token (classic)
5. Select the following scopes:
   - repo (Full control of private repositories)
     - repo:status
     - repo_deployment
     - public_repo
     - repo:invite
     - security_events
6. Copy the generated token to your `.env` file

## Usage

Basic usage (clone and generate documentation):
```bash
python repo_scanner.py <repository-url> <target-directory>
```

Create documentation and submit a pull request:
```bash
python repo_scanner.py <repository-url> <target-directory> --create-pr
```

Example:
```bash
python repo_scanner.py https://github.com/username/repo ./cloned_repo
```

## Output Structure

The tool creates a `documentation` directory in the cloned repository with the same structure as the source code. For example:

```
repository/
├── src/
│   ├── utils/
│   │   └── helper.py
│   └── main.py
└── documentation/
    ├── src/
    │   ├── utils/
    │   │   └── helper_docs.txt
    │   └── main_docs.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT No Attribution License (MIT-0) - see the [LICENSE](LICENSE) file for details.

The MIT-0 license allows you to:
- Use the code commercially
- Modify the code
- Distribute the code
- Use and modify the code in private

Without requiring you to:
- Include the original license
- Include copyright notices
- Make your modifications open source
- Provide attribution

The license also includes a strong disclaimer of liability.
