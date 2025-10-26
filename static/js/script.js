// Global variables for file management
let selectedFiles = [];

// Enhanced file upload handling
function updateFileName() {
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');
    const files = Array.from(fileInput.files);
    
    // Clear existing file list
    fileList.innerHTML = '';
    selectedFiles = [];
    
    if (files.length === 0) {
        fileList.innerHTML = '<p style="color: #bdc3c7; font-style: italic;">No files selected, Drag and Drop here</p>';
        return;
    }
    
    // Display each file as a removable item
    files.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>📄 ${file.name}</span>
            <button type="button" class="remove-file" onclick="removeFile(${index})" title="Remove file">×</button>
        `;
        fileList.appendChild(fileItem);
        selectedFiles.push(file);
    });
    
    // Update the upload button text
    const fileInputLabel = document.getElementById('fileInputLabel');
    fileInputLabel.innerHTML = `📁 ${files.length} file(s) selected - Click to change`;
}

// Remove individual file from selection
function removeFile(index) {
    selectedFiles.splice(index, 0);
    updateFileInput();
    updateFileName();
}

// Update the actual file input to match selected files
function updateFileInput() {
    const fileInput = document.getElementById('fileInput');
    const dataTransfer = new DataTransfer();
    
    selectedFiles.forEach(file => {
        dataTransfer.items.add(file);
    });
    
    fileInput.files = dataTransfer.files;
}

// Enhanced askAssistant function
async function askAssistant() {
    try {
        const question = document.getElementById('question').value.trim();
        const hints = document.getElementById('hints').value.trim();
        const fileInput = document.getElementById('fileInput');
        const files = fileInput.files;
        // get the conversation ID from the HTML
        const conversationId = document.querySelector('.conversation-info p').textContent.split('ID: ')[1];
        if (!question) {
            showError('Please enter a question.');
            return;
        }
        if (files.length === 0) {
            showError('Please upload at least one PDF file.');
            return;
        }

        showLoading(true);

        const responseContainer = document.getElementById('response');
        responseContainer.style.display = 'block';
        updateResponseContent('🔄 Processing your request...', 'processing');

        // Build the multipart form data
        const formData = new FormData();
        formData.append('hints', hints);
        formData.append('question', question);
        formData.append('conversation_id', conversationId);

        // Append all selected files under the same key “files”
        for (const file of files) {
            formData.append('files', file);
        }

        // POST to Flask
        const response = await fetch('/app/chat', {
            method: 'POST',
            body: formData,
            credentials: 'include' // VERY IMPORTANT for Flask-Login cookies!
        });

        const data = await response.json();
        showLoading(false);

        if (!response.ok || data.status === 'error') {
            const errorMessage = data.message || 'An error occurred while processing your request.';
            showError(errorMessage);
            return;
        }

        updateResponseContent(data.assistant_response, 'success');
    } catch (error) {
        console.error('Error:', error);
        showLoading(false);
        showError('An unexpected error occurred. Please try again.');
    }
}


// Enhanced clearChat function
function clearChat() {
    // Clear form inputs
    document.getElementById('hints').value = '';
    document.getElementById('question').value = '';
    
    // Clear file selection
    document.getElementById('fileInput').value = '';
    selectedFiles = [];
    updateFileName();
    
    // Clear response
    const responseContainer = document.getElementById('response');
    const responseContent = responseContainer.querySelector('.response-content');
    responseContent.innerHTML = '<p class="placeholder">Your AI assistant\'s response will appear here after you ask a question.</p>';
    
    // Hide any error messages
    hideError();
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.querySelector('.overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Update response content with proper formatting
function updateResponseContent(content, type = 'success') {
    const responseContainer = document.getElementById('response');
    const responseContent = responseContainer.querySelector('.response-content');
    
    if (type === 'processing') {
        responseContent.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #1a73e8; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <p style="margin-top: 1rem; color: #bdc3c7;">${content}</p>
            </div>
        `;
    } else {
        responseContent.innerHTML = `
            <div style="white-space: pre-wrap; line-height: 1.6;">${content}</div>
        `;
    }
}

// Show error message
function showError(message) {
    // Remove any existing error messages
    hideError();
    
    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.id = 'error-message';
    errorDiv.style.cssText = `
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        animation: fadeInUp 0.3s ease-out;
    `;
    errorDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span>⚠️</span>
            <span>${message}</span>
        </div>
    `;
    
    // Insert error message after the content section
    const contentSection = document.querySelector('.content');
    contentSection.parentNode.insertBefore(errorDiv, contentSection.nextSibling);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideError();
    }, 5000);
}

// Hide error message
function hideError() {
    const errorMessage = document.getElementById('error-message');
    if (errorMessage) {
        errorMessage.remove();
    }
}

// Add drag and drop functionality for file upload
function initializeDragAndDrop() {
    const fileInputLabel = document.getElementById('fileInputLabel');
    const fileList = document.getElementById('fileList');
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, preventDefaults, false);
        fileList.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    fileInputLabel.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    e.currentTarget.style.background = 'rgba(26, 115, 232, 0.1)';
    e.currentTarget.style.border = '2px dashed #1a73e8';
}

function unhighlight(e) {
    e.currentTarget.style.background = '';
    e.currentTarget.style.border = '';
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    // Update file input
    const fileInput = document.getElementById('fileInput');
    fileInput.files = files;
    
    // Update display
    updateFileName();
}

// Update copyright year dynamically
function updateCopyrightYear() {
    const currentYear = new Date().getFullYear();
    const copyrightElement = document.querySelector('.paragraph-container p');
    if (copyrightElement) {
        copyrightElement.innerHTML += ` <br> &copy; ${currentYear} HR Assistant. All rights reserved.`;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Update copyright year
    updateCopyrightYear();
    
    // Initialize drag and drop
    initializeDragAndDrop();
    
    // Set up file input change handler
    document.getElementById('fileInput').addEventListener('change', updateFileName);
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            askAssistant();
        }
        
        // Escape to clear
        if (e.key === 'Escape') {
            clearChat();
        }
    });
    
    // Add form validation on input
    const questionInput = document.getElementById('question');
    const hintsInput = document.getElementById('hints');
    
    [questionInput, hintsInput].forEach(input => {
        input.addEventListener('input', function() {
            // Remove any existing error styling
            this.style.borderColor = '';
            this.style.boxShadow = '';
        });
    });
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .file-item {
        animation: fadeInUp 0.3s ease-out;
    }
    
    .remove-file:hover {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
    }
`;
document.head.appendChild(style);