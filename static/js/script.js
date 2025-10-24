

async function askAssistant() {
  try {
    // Show loading overlay
    document.querySelector('.overlay').style.display = 'flex';
    document.querySelector('.response-container').style.display = 'flex';

    const question = document.getElementById('question').value;
    const hints = document.getElementById('hints').value;
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

    const formData = new FormData();
    formData.append('hints', hints);
    formData.append('question', question);

    for (const file of files) {
      formData.append('files', file);
    }

    const response = await fetch('/app/chat', {
      method: 'POST',
      body: formData,
    });

    // Hide loading overlay after fetching data
    document.querySelector('.overlay').style.display = 'none';

    const data = await response.json();

    if (!response.ok || data.status === 'error') {
      // Display an error message to the user
      if (data.errors && Array.isArray(data.errors)) {
        alert(`Error: ${data.message}\nDetails: ${data.errors.join(', ')}`);
      } else {
        alert(`Error: ${data.message}`);
      }
      return;
    }

    document.getElementById('response').innerText = `Assistant: ${data.assistant_response}`;
  } catch (error) {
    // Handle unexpected errors
    console.error(error);
    // Display an error message to the user
    alert(data.message);
  }
}



/*Clears the chat input fields.*/
function clearChat() {
    const hintsTextarea = document.getElementById('hints');
    hintsTextarea.value = '';
    const questionTextarea = document.getElementById('question');
    questionTextarea.value = '';
  }


/* Updates the file name displayed in the file input label.*/
function updateFileName() {
    const fileInput = document.getElementById('fileInput');
    const fileInputLabel = document.getElementById('fileInputLabel');
    const fileNames = Array.from(fileInput.files).map(file => file.name).join(', ') || 'No files chosen';
    fileInputLabel.querySelector('span').innerText = fileNames;
  }

