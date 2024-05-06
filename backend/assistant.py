import openai
import time,os

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Set  OpenAI API key --MAKE THE OPENAI_API_KEY ENV VARIABLE
# change the sensitive data if published
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY


def assistant(hints,question,file_contents):
    start_time = time.time()
    # Stream messages to ask a question about the files
    assistant_messages = [
        {"role": "system", "content": "You are a HR Specialist."},
        {"role": "user", "content": hints},
        {"role": "user", "content": f"Files: {file_contents}\n\nQuestion: {question}?"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-instruct",
        messages=assistant_messages,
        temperature=0.5  # Adjust temperature as needed
    )
    # Measure the end time
    end_time = time.time()
    # Print the total time taken
    print(f"Total time taken: {end_time - start_time} seconds")

    assistant_response = response['choices'][0]['message']['content']

    return assistant_response

    
