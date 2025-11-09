import openai
import time
import os

from openai import RateLimitError, APIError
# Load environment variables from .env file 
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Set OpenAI API key --MAKE THE OPENAI_API_KEY ENV VARIABLE
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY


def assistant(hints: str, question: str, file_content: str) -> str:
    # Call assistant function
    try:
        start_time = time.time()
        # Stream messages to ask a question about the files
        assistant_messages = [
            {"role": "system", "content": "You are a HR Specialist."},
            {"role": "user", "content": hints},
            {"role": "user", "content": f"Files: {file_content}\n\nQuestion: {question}?"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-instruct",
            messages=assistant_messages,
            temperature=0.5 
        )
        # Measure the end time
        end_time = time.time()
        # Print the total time taken
        print(f"{assistant.__name__}: Total time taken: {end_time - start_time} seconds")

        assistant_response = response['choices'][0]['message']['content']

        return assistant_response
    
    except RateLimitError as e:
        print(f"{assistant.__name__}: OpenAI Rate limit error: {str(e)}")
        raise RateLimitError("OpenAI API rate limit exceeded") from e
    except APIError as e:
        print(f"{assistant.__name__}: OpenAI API error: {str(e)}")
        raise APIError("OpenAI API error occurred") from e
    except Exception as e:
        print(f"{assistant.__name__}: Assistant error: {str(e)}")
        raise Exception("An error occurred in the assistant function") from e

    
