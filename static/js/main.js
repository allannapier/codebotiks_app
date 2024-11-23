document.addEventListener('DOMContentLoaded', function() {
    loadDocumentationFiles();
});

async function loadDocumentationFiles() {
    try {
        const response = await fetch('/api/docs');
        const files = await response.json();
        
        // Group files by directory
        const groupedFiles = groupFilesByDirectory(files);
        
        // Render file list
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = ''; // Clear existing content
        
        Object.entries(groupedFiles).forEach(([directory, files]) => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'file-group';
            
            // Add directory name if not root
            if (directory !== '/') {
                const dirName = document.createElement('div');
                dirName.className = 'directory-name';
                dirName.textContent = directory;
                groupDiv.appendChild(dirName);
            }
            
            // Add files
            files.forEach(file => {
                const fileDiv = document.createElement('div');
                fileDiv.className = 'file-item';
                fileDiv.textContent = file.name;
                fileDiv.addEventListener('click', () => loadDocumentContent(file.path));
                groupDiv.appendChild(fileDiv);
            });
            
            fileList.appendChild(groupDiv);
        });
    } catch (error) {
        console.error('Error loading documentation files:', error);
    }
}

function groupFilesByDirectory(files) {
    return files.reduce((groups, file) => {
        const dir = file.directory;
        if (!groups[dir]) {
            groups[dir] = [];
        }
        groups[dir].push(file);
        return groups;
    }, {});
}

async function loadDocumentContent(filePath) {
    try {
        // Update active file in sidebar
        const fileItems = document.querySelectorAll('.file-item');
        fileItems.forEach(item => item.classList.remove('active'));
        event.target.classList.add('active');
        
        // Load and display content
        const response = await fetch(`/api/doc/${filePath}`);
        const data = await response.json();
        
        const contentDiv = document.getElementById('documentContent');
        contentDiv.innerHTML = data.content;
        
        // Apply syntax highlighting to code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
    } catch (error) {
        console.error('Error loading document content:', error);
    }
}
