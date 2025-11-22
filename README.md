## HR Assistant Web Application

HR Assistant is a web application that provides assistance to HR professionals in making better hiring decisions. It allows users to upload PDF documents containing candidate's information, provide hints or instructions to guide the assistant, ask questions about the content of the PDFs using a chat interface, and receive relevant answers from the HR Assistant.

## Installation

**To run the HR Assistant web application locally, follow these steps:**


**1-Clone the repository**

    git clone https://github.com/Soni912108/hr_assistant.git


**2-Create a virtual environment:**

*On Windows:*
        
    python -m venv venv

*On macOS and Linux:*

    python3 -m venv .venv

**3-Activate the virtual environment:**

*On Windows:*

    venv\Scripts\activate

*On macOS and Linux:*
    
    source venv/bin/activate
  
**5-Install the required Python packages:**

    pip install -r requirements.txt


## Usage:

**1-Start the Flask development server:**

    python app.py

**2-On start of the server open your web browser and navigate to http://localhost:5000 to access the HR Assistant web application.**



## NOTE:
Make sure to have an OpenAI account and create a API KEY to pass to your .env file, along side with the other sensitive data

