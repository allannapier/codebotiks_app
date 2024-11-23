"""Repository documentation generator using Google's Gemini AI."""

import os
from pathlib import Path
from typing import Tuple, Optional, Union, List
import git
import argparse
import shutil
import platform
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
from github import Github
from datetime import datetime
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Only configure Gemini if API key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

def extract_repo_info(repo_url: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract owner and repository name from GitHub URL.
    
    Args:
        repo_url: GitHub repository URL.
        
    Returns:
        Tuple containing owner and repository name, or (None, None) if invalid.
    """
    try:
        parts = repo_url.strip('/').split('/')
        if len(parts) >= 5 and parts[2] == 'github.com':
            owner = parts[3]
            repo = parts[4]
            # Remove .git extension if present
            if repo.endswith('.git'):
                repo = repo[:-4]
            return owner, repo
    except:
        pass
    return None, None

def create_pull_request(repo_path: str, repo_url: str, branch_name: Optional[str] = None) -> bool:
    """Create a pull request with the documentation changes.
    
    Args:
        repo_path: Path to local repository.
        repo_url: GitHub repository URL.
        branch_name: Optional branch name for PR (default: docs/auto-generated-docs).
        
    Returns:
        True if PR was created successfully, False otherwise.
    """
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("GitHub token not found. Please set GITHUB_TOKEN environment variable.")
        return False

    try:
        # Initialize GitHub client
        g = Github(token)
        
        # Extract owner and repo from URL
        owner, repo_name = extract_repo_info(repo_url)
        if not owner or not repo_name:
            print("Invalid repository URL")
            return False
        
        # Get repository
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Create branch
        if not branch_name:
            branch_name = 'docs/auto-generated-docs'
        
        # Create and push branch
        git_repo = git.Repo(repo_path)
        branch = git_repo.create_head(branch_name)
        branch.checkout()
        
        # Stage all new files
        git_repo.git.add(all=True)
        
        # Commit changes
        commit_message = "Add auto-generated documentation"
        git_repo.index.commit(commit_message)
        
        # Push changes
        git_repo.git.push('--set-upstream', 'origin', branch_name)

        # Create pull request
        pr = repo.create_pull(
            title="Add Auto-Generated Documentation",
            body="This PR adds automatically generated documentation for Python files.",
            head=branch_name,
            base=repo.default_branch
        )
        
        print(f"Created pull request: {pr.html_url}")
        return True
        
    except Exception as e:
        print(f"Error creating pull request: {str(e)}")
        return False

def remove_directory(path: Union[str, Path]) -> bool:
    """Remove a directory using the appropriate method for the current OS.
    
    Args:
        path: Directory path to remove.
        
    Returns:
        True if directory was removed successfully, False otherwise.
    """
    if platform.system() == 'Windows':
        try:
            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', str(path)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error removing directory using Windows command: {e}")
            return False
    else:
        try:
            shutil.rmtree(str(path))
        except Exception as e:
            print(f"Error removing directory: {e}")
            return False
    return True

def analyze_python_file(file_path: Union[str, Path]) -> str:
    """Analyze a Python file and generate documentation using Google's Gemini AI.
    
    Args:
        file_path: Path to Python file.
        
    Returns:
        Generated documentation as markdown text.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate documentation using Gemini
        prompt = f"""
        Analyze this Python code and generate detailed markdown documentation:

        {content}

        Include:
        1. Overview of functionality
        2. Key components and their purpose
        3. Usage examples if applicable
        4. Dependencies and requirements
        5. Notable design decisions
        """
        
        if model is None:
            return "Error: Gemini API key not available"
        
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def create_documentation_file(python_file_path: Union[str, Path], repo_path: Union[str, Path], analysis: str) -> bool:
    """Create a documentation markdown file for the analyzed Python file.
    
    Args:
        python_file_path: Path to Python file.
        repo_path: Path to repository root.
        analysis: Generated documentation content.
        
    Returns:
        True if documentation was created successfully, False otherwise.
    """
    try:
        # Get the relative path of the Python file from the repo root
        relative_path = os.path.relpath(str(python_file_path), str(repo_path))
        
        # Create the documentation path with the same structure
        doc_path = os.path.join(str(repo_path), 'documentation', os.path.dirname(relative_path))
        doc_file_name = os.path.basename(relative_path).replace('.py', '_docs.md')
        doc_file_path = os.path.join(doc_path, doc_file_name)
        
        # Create the directory structure if it doesn't exist
        try:
            os.makedirs(doc_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating documentation directory: {str(e)}")
            return False
        
        try:
            with open(doc_file_path, 'w', encoding='utf-8') as file:
                file.write(f"# Documentation for `{os.path.basename(python_file_path)}`\n\n")
                file.write("---\n\n")
                file.write(analysis)
                file.write("\n\n---\n*Documentation generated automatically using Google's Gemini AI*")
            print(f"Created documentation: {os.path.relpath(doc_file_path, str(repo_path))}")
            return True
        except Exception as e:
            print(f"Error writing documentation file: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error creating documentation file: {str(e)}")
        return False

def clone_repository(repo_url: str, target_dir: Union[str, Path]) -> bool:
    """Clone a repository from the given URL to the target directory.
    
    Args:
        repo_url: GitHub repository URL.
        target_dir: Directory to clone into.
        
    Returns:
        True if repository was cloned successfully, False otherwise.
    """
    try:
        # Check if directory exists and remove it if it does
        if os.path.exists(target_dir):
            print(f"Removing existing directory: {target_dir}")
            if not remove_directory(target_dir):
                return False
        
        # Clone the repository
        git.Repo.clone_from(repo_url, str(target_dir))
        print(f"Successfully cloned repository to {target_dir}")
        return True
    except git.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def scan_repository(repo_path: Union[str, Path]) -> None:
    """Scan through all files in the repository and analyze Python files.
    
    Args:
        repo_path: Path to repository root.
    """
    repo_path = Path(repo_path)
    if not repo_path.exists():
        print(f"Repository path {repo_path} does not exist")
        return

    # Create the documentation directory
    doc_dir = repo_path / 'documentation'
    os.makedirs(doc_dir, exist_ok=True)

    for root, dirs, files in os.walk(repo_path):
        # Skip documentation directory itself
        if 'documentation' in dirs:
            dirs.remove('documentation')
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        # Skip __pycache__ directory
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            print(f"Found file: {relative_path}")
            
            # If it's a Python file, analyze it
            if file.endswith('.py'):
                print(f"Analyzing Python file: {relative_path}")
                analysis = analyze_python_file(file_path)
                create_documentation_file(file_path, repo_path, analysis)

def main() -> None:
    """Main entry point for the repository documentation generator."""
    parser = argparse.ArgumentParser(description='Clone and scan a git repository')
    parser.add_argument('repo_url', help='URL of the repository to clone')
    parser.add_argument('target_dir', help='Directory to clone the repository into')
    parser.add_argument('--create-pr', action='store_true', help='Create a pull request with the documentation changes')
    parser.add_argument('--serve', action='store_true', help='Start the documentation web server after generation')
    parser.add_argument('--port', type=int, default=5000, help='Port for the documentation server (default: 5000)')
    
    args = parser.parse_args()
    
    if clone_repository(args.repo_url, args.target_dir):
        print("\nScanning repository files...")
        scan_repository(args.target_dir)
        
        if args.create_pr:
            print("\nCreating pull request...")
            create_pull_request(args.target_dir, args.repo_url)
        
        if args.serve:
            print("\nStarting documentation server...")
            from doc_server import start_server
            start_server(args.port)

if __name__ == "__main__":
    main()
