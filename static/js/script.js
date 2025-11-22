// Global variables for file management
let selectedFiles = [];
let currentFileId = null;
let currentConversationId = document.querySelector('.conversation-info').dataset.conversationId;


// add upload guard + debounce
let uploadInProgress = false;
let uploadTimer = null;
const UPLOAD_DEBOUNCE_MS = 150;

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
        // Reset file and conversation IDs when no file is selected
        currentFileId = null;
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
    
    // Debounced auto-upload to prevent duplicate calls from multiple events
    if (files.length > 0) {
        if (uploadTimer) clearTimeout(uploadTimer);
        uploadTimer = setTimeout(() => {
            // only start if not already uploading
            if (!uploadInProgress) {
                uploadFile();
            }
        }, UPLOAD_DEBOUNCE_MS);
    }
}

// Remove individual file from selection
function removeFile(index) {
    selectedFiles.splice(index, 1);
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

// Upload file function - called when files are selected
async function uploadFile() {
    try {
        const fileInput = document.getElementById('fileInput');
        const files = fileInput.files;

        if (files.length === 0) {
            return; // No files to upload
        }

        showLoading(true);

        // Build form data for file upload
        const formData = new FormData();
        formData.append('files', files[0]);
        formData.append('conversation_id', currentConversationId);

        // POST to upload endpoint
        const response = await fetch('/app/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        const data = await response.json();
        showLoading(false);

        if (!response.ok || data.status === 'error') {
            const errorMessage = data.message || 'An error occurred while uploading the file.';
            showError(errorMessage);
            currentFileId = null;
            return;
        }
        currentFileId = data.file_id;
        // Show success notification
        const successMessage = `✅ File uploaded successfully! File ID: ${currentFileId}. You can now ask questions about this file.`;
        showSuccess(successMessage);

        // Clear previous chat messages and reveal response area
        const responseContainer = document.getElementById('response');
        const responseContent = responseContainer.querySelector('.response-content');
        responseContent.innerHTML = ''; // Clear previous messages for new conversation
        responseContainer.style.display = 'block';

    } catch (error) {
        console.error('Error uploading file:', error);
        showLoading(false);
        showError('An unexpected error occurred while uploading the file.');
        currentFileId = null;
    } finally {
        // release guard (small delay to avoid immediate re-trigger)
        setTimeout(() => { uploadInProgress = false; }, 250);
    }
}

// askAssistant function
async function askAssistant() {
    try {
        const question = document.getElementById('question').value.trim();
        const hints = document.getElementById('hints').value.trim();

        if (!question) {
            showError('Please enter a question.');
            return;
        }

        if (!currentFileId || !currentConversationId) {
            showError('Please upload a file first before asking questions.');
            return;
        }

        showLoading(true);

        const responseContainer = document.getElementById('response');
        responseContainer.style.display = 'block';
        updateResponseContent('🔄 Processing your request...', 'processing');

        // Build JSON data for chat request
        const chatData = {
            hints: hints,
            question: question,
            file_id: currentFileId.toString(),
            conversation_id: currentConversationId.toString()
        };

        // POST to chat endpoint
        const response = await fetch('/app/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(chatData),
            credentials: 'include'
        });

        const data = await response.json();
        showLoading(false);

        if (!response.ok || data.status === 'error') {
            const errorMessage = data.message || 'An error occurred while processing your request.';
            showError(errorMessage);
            showLoading(false);
            return;
        }

        // Display question and answer
        displayChatMessage(question, data.assistant_response);
        
    } catch (error) {
        console.error('Error:', error);
        showLoading(false);
        showError('An unexpected error occurred. Please try again.');
    }
}

// Display chat message 
function displayChatMessage(question, answer) {
    const responseContainer = document.getElementById('response');
    const responseContent = responseContainer.querySelector('.response-content');
    
    // Clear processing message if it exists and remove spinner and processing text
    // Check for the processing indicator div structure
    const processingDiv = responseContent.querySelector('div[style*="text-align: center"]');
    if (processingDiv) {
        responseContent.innerHTML = ''; // Clear processing message
    }
    
    // Create a new message entry
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';
    messageDiv.style.cssText = `
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        background: #fafafa;
        animation: fadeInUp 0.3s ease-out;
    `;
    
    messageDiv.innerHTML = `
        <div style="margin-bottom: 0.5rem;">
            <strong style="color: #1a73e8;">You:</strong>
            <div style="margin-left: 1rem; margin-top: 0.25rem; color: #333;">${escapeHtml(question)}</div>
        </div>
        <div>
            <strong style="color: #34a853;">Assistant:</strong>
            <div style="margin-left: 1rem; margin-top: 0.25rem; color: #333; white-space: pre-wrap;">${escapeHtml(answer)}</div>
        </div>
    `;
    
    // Append to response content (accumulate messages)
    responseContent.appendChild(messageDiv);
    
    // Scroll to bottom
    responseContent.scrollTop = responseContent.scrollHeight;
}

// Helper function to escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// clearChat function
function clearChat() {
    // Clear form inputs
    document.getElementById('hints').value = '';
    document.getElementById('question').value = '';
    
    // Clear file selection
    document.getElementById('fileInput').value = '';
    selectedFiles = [];
    
    // Reset file and conversation IDs
    currentFileId = null;
    currentConversationId = null;
    
    // Update file display
    updateFileName();
    
    // Clear response and reset to initial state
    const responseContainer = document.getElementById('response');
    const responseContent = responseContainer.querySelector('.response-content');
    responseContent.innerHTML = '<p class="placeholder">Your AI assistant\'s response will appear here after you ask a question.</p>';
    
    // Reset conversation info display
    const conversationInfo = document.querySelector('.conversation-info p');
    if (conversationInfo) {
        const initialId = document.querySelector('.conversation-info p')?.textContent.split('ID: ')[1]?.split(' |')[0] || 'None';
        conversationInfo.textContent = `ID: ${initialId}`;
    }
    
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

function showSuccess(message) {
    hideSuccess(); // remove any existing success message

    const successDiv = document.createElement('div');
    successDiv.id = 'success-message';
    successDiv.style.cssText = `
        background: linear-gradient(135deg, #34a853 0%, #28a745 100%);
        color: white;
        padding: 0.9rem 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.25);
        animation: fadeInUp 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    `;
    successDiv.innerHTML = `
        <span>✅</span>
        <span>${message}</span>
    `;

    // Insert success message at the top of the section with id="content"
    const contentSectionById = document.getElementById('content');
    if (contentSectionById) {
        contentSectionById.insertBefore(successDiv, contentSectionById.firstChild);
    } else {
        // fallback: insert after .content section
        const contentSection = document.querySelector('.content');
        if (contentSection && contentSection.parentNode) {
            contentSection.parentNode.insertBefore(successDiv, contentSection);
        } else {
            document.body.insertBefore(successDiv, document.body.firstChild);
        }
    }

    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideSuccess();
    }, 5000);
}

function hideSuccess() {
    const existing = document.getElementById('success-message');
    if (existing) existing.remove();
}

// Drag and drop functionality for file upload
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
    
    // Update display (this will also trigger file upload)
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
