import os
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import git
from repo_scanner import (
    extract_repo_info,
    create_pull_request,
    remove_directory,
    analyze_python_file,
    create_documentation_file,
    clone_repository,
    scan_repository,
    main
)

def test_extract_repo_info():
    """Test repository info extraction from URLs"""
    # Test valid URLs
    assert extract_repo_info('https://github.com/user/repo') == ('user', 'repo')
    assert extract_repo_info('https://github.com/user/repo.git') == ('user', 'repo')  # Should strip .git
    
    # Test invalid URLs
    assert extract_repo_info('https://github.com/user') == (None, None)
    assert extract_repo_info('invalid_url') == (None, None)

@patch('repo_scanner.Github')
@patch('git.Repo')
def test_create_pull_request(mock_git_repo, mock_github):
    """Test pull request creation"""
    # Mock Git repository
    mock_repo = Mock()
    mock_git_repo.return_value = mock_repo
    mock_repo.create_head.return_value = Mock()
    
    # Mock GitHub repository
    mock_github_instance = Mock()
    mock_github.return_value = mock_github_instance
    mock_github_repo = Mock()
    mock_github_instance.get_repo.return_value = mock_github_repo
    mock_github_repo.create_pull.return_value = Mock(html_url='https://github.com/user/repo/pull/1')
    
    # Test successful PR creation
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'dummy_token'}):
        result = create_pull_request('/path/to/repo', 'https://github.com/user/repo')
        assert result is True

    # Test missing token
    with patch.dict('os.environ', {'GITHUB_TOKEN': ''}):
        result = create_pull_request('/path/to/repo', 'https://github.com/user/repo')
        assert result is False

@patch('subprocess.run')
@patch('shutil.rmtree')
def test_remove_directory(mock_rmtree, mock_subprocess_run):
    """Test directory removal"""
    # Test Windows removal
    with patch('platform.system', return_value='Windows'):
        mock_subprocess_run.return_value = Mock(returncode=0)
        assert remove_directory('test_dir') is True
        
        mock_subprocess_run.side_effect = Exception('Error')
        try:
            remove_directory('test_dir')
            assert False, "Should have raised an exception"
        except:
            pass
    
    # Test Unix removal
    with patch('platform.system', return_value='Linux'):
        mock_rmtree.side_effect = None
        assert remove_directory('test_dir') is True
        
        mock_rmtree.side_effect = Exception('Error')
        try:
            remove_directory('test_dir')
            assert False, "Should have raised an exception"
        except:
            pass

@patch('repo_scanner.model')
def test_analyze_python_file(mock_model):
    """Test Python file analysis"""
    # Mock successful analysis
    mock_model.generate_content.return_value = Mock(text='Generated documentation')
    
    with patch('builtins.open', mock_open(read_data='def test(): pass')):
        result = analyze_python_file('test.py')
        assert result == 'Generated documentation'
        mock_model.generate_content.assert_called_once()
    
    # Test file read error
    with patch('builtins.open', side_effect=Exception('Error')):
        result = analyze_python_file('nonexistent.py')
        assert 'Error analyzing file' in result

def test_create_documentation_file(tmp_path):
    """Test documentation file creation"""
    repo_path = tmp_path / 'repo'
    python_file = repo_path / 'test.py'
    repo_path.mkdir()
    
    analysis = 'Test documentation content'
    create_documentation_file(str(python_file), str(repo_path), analysis)
    
    doc_file = repo_path / 'documentation' / 'test_docs.md'
    assert doc_file.exists()
    assert 'Test documentation content' in doc_file.read_text()

@patch('os.makedirs')
def test_create_documentation_file_errors(mock_makedirs, tmp_path):
    """Test error handling in documentation file creation"""
    repo_path = tmp_path / 'repo'
    python_file = repo_path / 'test.py'
    
    # Test makedirs error
    mock_makedirs.side_effect = Exception('Permission denied')
    result = create_documentation_file(str(python_file), str(repo_path), 'test')
    assert result is False
    mock_makedirs.assert_called_once()
    
    # Test file write error
    mock_makedirs.side_effect = None
    with patch('builtins.open', side_effect=Exception('Write error')):
        result = create_documentation_file(str(python_file), str(repo_path), 'test')
        assert result is False

@patch('git.Repo')
def test_clone_repository(mock_git_repo, tmp_path):
    """Test repository cloning"""
    # Test successful clone
    mock_git_repo.clone_from.return_value = Mock()
    assert clone_repository('https://github.com/user/repo', str(tmp_path)) is True
    
    # Test clone error
    mock_git_repo.clone_from.side_effect = git.GitCommandError('clone', 'error')
    assert clone_repository('https://github.com/user/repo', str(tmp_path)) is False

@patch('repo_scanner.analyze_python_file')
def test_scan_repository(mock_analyze, tmp_path):
    """Test repository scanning"""
    # Create test repository structure
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / 'test.py').write_text('print("test")')
    (repo_path / 'subdir').mkdir()
    (repo_path / 'subdir' / 'test2.py').write_text('print("test2")')
    
    mock_analyze.return_value = 'Test documentation'
    
    scan_repository(str(repo_path))
    
    # Check if documentation files were created
    assert (repo_path / 'documentation' / 'test_docs.md').exists()
    assert (repo_path / 'documentation' / 'subdir' / 'test2_docs.md').exists()

@patch('repo_scanner.analyze_python_file')
@patch('repo_scanner.create_documentation_file')
def test_scan_repository_edge_cases(mock_create_docs, mock_analyze, tmp_path):
    """Test edge cases in repository scanning"""
    # Test non-existent directory
    scan_repository(str(tmp_path / 'nonexistent'))
    mock_analyze.assert_not_called()
    
    # Test empty directory
    repo_path = tmp_path / 'empty_repo'
    repo_path.mkdir()
    scan_repository(str(repo_path))
    mock_analyze.assert_not_called()
    
    # Test with special directories
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()
    (repo_path / '.git').mkdir()
    (repo_path / '__pycache__').mkdir()
    (repo_path / 'documentation').mkdir()
    (repo_path / 'test.py').write_text('print("test")')
    
    mock_analyze.return_value = 'Test documentation'
    scan_repository(str(repo_path))
    mock_analyze.assert_called_once()

@patch('doc_server.start_server')
@patch('repo_scanner.scan_repository')
@patch('repo_scanner.clone_repository')
@patch('repo_scanner.create_pull_request')
def test_main_function(mock_pr, mock_clone, mock_scan, mock_server):
    """Test main function CLI handling"""
    # Test basic clone and scan
    mock_clone.return_value = True
    with patch('sys.argv', ['repo_scanner.py', 'https://github.com/user/repo', '/tmp/repo']):
        main()
        mock_clone.assert_called_once()
        mock_scan.assert_called_once()
        mock_pr.assert_not_called()
        mock_server.assert_not_called()
    
    # Test with create PR
    mock_clone.reset_mock()
    mock_scan.reset_mock()
    with patch('sys.argv', ['repo_scanner.py', 'https://github.com/user/repo', '/tmp/repo', '--create-pr']):
        main()
        mock_clone.assert_called_once()
        mock_scan.assert_called_once()
        mock_pr.assert_called_once()
        mock_server.assert_not_called()
    
    # Test with serve option
    mock_clone.reset_mock()
    mock_scan.reset_mock()
    mock_pr.reset_mock()
    with patch('sys.argv', ['repo_scanner.py', 'https://github.com/user/repo', '/tmp/repo', '--serve', '--port', '8000']):
        main()
        mock_clone.assert_called_once()
        mock_scan.assert_called_once()
        mock_pr.assert_not_called()
        mock_server.assert_called_once_with(8000)
    
    # Test clone failure
    mock_clone.reset_mock()
    mock_scan.reset_mock()
    mock_server.reset_mock()
    mock_clone.return_value = False
    with patch('sys.argv', ['repo_scanner.py', 'https://github.com/user/repo', '/tmp/repo']):
        main()
        mock_clone.assert_called_once()
        mock_scan.assert_not_called()
        mock_pr.assert_not_called()
        mock_server.assert_not_called()
