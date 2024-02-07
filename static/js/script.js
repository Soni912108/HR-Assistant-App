/**
 * Sends the question and code snippet to the code assistant for analysis.
 */
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

    const response = await fetch('/chat', {
      method: 'POST',
      body: formData,
    });

    // Hide loading overlay after fetching data
    document.querySelector('.overlay').style.display = 'none';

    const data = await response.json();

    if (!response.ok || data.status === 'error') {
      // Display an error message to the user
      alert(data.message);
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



/**
 * Clears the chat input fields.
 */
function clearChat() {
    /**
     * The text area for the hints.
     * @type {HTMLTextAreaElement}
     */
    const hintsTextarea = document.getElementById('hints');
    hintsTextarea.value = '';
  
    /**
     * The text area for the question.
     * @type {HTMLTextAreaElement}
     */
    const questionTextarea = document.getElementById('question');
    questionTextarea.value = '';
  }


/**
 * Updates the file name displayed in the file input label.
 */
function updateFileName() {
    const fileInput = document.getElementById('fileInput');
    const fileInputLabel = document.getElementById('fileInputLabel');
    const fileNames = Array.from(fileInput.files).map(file => file.name).join(', ') || 'No files chosen';
    fileInputLabel.querySelector('span').innerText = fileNames;
  }



// Select the buttons and form
const contactButton = document.getElementById("contact");
const contactForm = document.getElementById("contact-form");
const sendButton = document.getElementById("send");
const cancelButton = document.getElementById("cancel");

// Toggle the form visibility on button click
contactButton.addEventListener("click", () => {
  contactForm.style.display = contactForm.style.display === "none" ? "block" : "none";
  contactButton.style.display = contactForm.style.display === "none" ? "block" : "none";
});

// Handle form submission
sendButton.addEventListener("click", (event) => {
  event.preventDefault();

  // Get form data
  const email = document.querySelector("input[name='email']").value;
  const message = document.querySelector("textarea[name='message']").value;

  // Send form data to the server 
  fetch("/new_contact_form", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ email, message })
  })
  .then(response => response.json())
  .then(data => {
    // Handle response from server
    console.log("Form submitted successfully:", data);
    contactForm.reset(); // Clear form fields
    contactForm.style.display = "none"; // Hide form
    contactButton.style.display = "block"; // Show "Contact Support" button again
  })
  .catch(error => {
    console.error("Error submitting form:", error);
  });
});

// Handle form cancellation
cancelButton.addEventListener("click", () => {
  contactForm.reset(); // Clear form fields
  contactForm.style.display = "none"; // Hide form
  contactButton.style.display = "block"; // Show "Contact Support" button again
});
