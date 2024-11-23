import os
import git
import argparse
import shutil
import platform
import subprocess
from pathlib import Path
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

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def extract_repo_info(repo_url):
    """
    Extract owner and repo name from GitHub URL
    """
    path = urlparse(repo_url).path
    parts = path.strip('/').split('/')
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None

def create_pull_request(repo_path, repo_url, branch_name=None):
    """
    Create a pull request with the documentation changes
    """
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not found in environment variables. Skipping pull request creation.")
        return False

    try:
        # Initialize repository
        repo = git.Repo(repo_path)
        
        # Create a unique branch name with timestamp
        if branch_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"docs/auto-generated_{timestamp}"
        
        # Create and checkout new branch
        current = repo.create_head(branch_name)
        current.checkout()

        # Stage all new files
        repo.git.add(all=True)
        
        # Commit changes
        commit_message = "Add auto-generated documentation"
        repo.index.commit(commit_message)
        
        # Push changes
        repo.git.push('--set-upstream', 'origin', branch_name)

        # Create pull request using GitHub API
        g = Github(GITHUB_TOKEN)
        owner, repo_name = extract_repo_info(repo_url)
        if not owner or not repo_name:
            print("Could not extract owner and repo name from URL")
            return False

        github_repo = g.get_repo(f"{owner}/{repo_name}")
        pr = github_repo.create_pull(
            title="Add Auto-generated Documentation",
            body="This PR adds automatically generated documentation for Python files in the repository.",
            head=branch_name,
            base="main"  # or 'master' depending on the default branch
        )
        print(f"Created pull request: {pr.html_url}")
        return True

    except Exception as e:
        print(f"Error creating pull request: {e}")
        return False

def remove_directory(path):
    """
    Remove a directory using the appropriate method for the current OS
    """
    if platform.system() == 'Windows':
        try:
            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error removing directory using Windows command: {e}")
            return False
    else:
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f"Error removing directory: {e}")
            return False
    return True

def analyze_python_file(file_path):
    """
    Analyze a Python file using Google's Gemini API
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        prompt = f"""Analyze this Python code and provide a detailed documentation in markdown format that includes:
        # Overview
        - Brief description of the code's purpose
        
        # Key Components
        ## Functions
        - List and describe main functions and their purposes
        
        ## Dependencies
        - List key dependencies and their roles
        
        ## Variables
        - Document important variables and their roles
        
        ## Design Patterns & Architecture
        - Notable patterns or design choices
        - Code organization insights
        
        Here's the code:
        {content}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def create_documentation_file(python_file_path, repo_path, analysis):
    """
    Create a documentation markdown file for the analyzed Python file,
    maintaining the same directory structure under the documentation folder
    """
    # Get the relative path of the Python file from the repo root
    relative_path = os.path.relpath(python_file_path, repo_path)
    
    # Create the documentation path with the same structure
    doc_path = os.path.join(repo_path, 'documentation', os.path.dirname(relative_path))
    doc_file_name = os.path.basename(relative_path).replace('.py', '_docs.md')
    doc_file_path = os.path.join(doc_path, doc_file_name)
    
    # Create the directory structure if it doesn't exist
    os.makedirs(doc_path, exist_ok=True)
    
    try:
        with open(doc_file_path, 'w', encoding='utf-8') as file:
            file.write(f"# Documentation for `{os.path.basename(python_file_path)}`\n\n")
            file.write("---\n\n")
            file.write(analysis)
            file.write("\n\n---\n*Documentation generated automatically using Google's Gemini AI*")
        print(f"Created documentation: {os.path.relpath(doc_file_path, repo_path)}")
    except Exception as e:
        print(f"Error creating documentation file: {str(e)}")

def clone_repository(repo_url, target_dir):
    """
    Clone a repository from the given URL to the target directory.
    If the directory exists, it will be removed first.
    """
    try:
        # Check if directory exists and remove it if it does
        if os.path.exists(target_dir):
            print(f"Removing existing directory: {target_dir}")
            if not remove_directory(target_dir):
                return False
        
        # Clone the repository
        git.Repo.clone_from(repo_url, target_dir)
        print(f"Successfully cloned repository to {target_dir}")
        return True
    except git.GitCommandError as e:
        print(f"Error cloning repository: {e}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def scan_repository(repo_path):
    """
    Scan through all files in the repository and analyze Python files
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

def main():
    parser = argparse.ArgumentParser(description='Clone and scan a git repository')
    parser.add_argument('repo_url', help='URL of the repository to clone')
    parser.add_argument('target_dir', help='Directory to clone the repository into')
    parser.add_argument('--create-pr', action='store_true', help='Create a pull request with the documentation changes')
    
    args = parser.parse_args()
    
    if clone_repository(args.repo_url, args.target_dir):
        print("\nScanning repository files...")
        scan_repository(args.target_dir)
        
        if args.create_pr:
            print("\nCreating pull request...")
            create_pull_request(args.target_dir, args.repo_url)

if __name__ == "__main__":
    main()
