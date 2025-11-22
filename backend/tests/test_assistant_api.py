import os
import pytest
from openai import OpenAI, RateLimitError, APIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY").strip()

# List of models to test
MODELS_TO_TEST = ["gpt-3.5-turbo"]

@pytest.fixture(scope="module")
def openai_client():
    """Return an OpenAI client instance."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    return client

@pytest.mark.parametrize("model_name", MODELS_TO_TEST)
def test_openai_multiple_models(openai_client, model_name):
    """Test OpenAI API key with multiple models and print responses."""
    print(f"\n▶️ Testing model: {model_name}")

    try:
        response = openai_client.chat.completions.create(
            model=model_name.strip(),
            messages=[{"role": "user", "content": "Say hello"}],
        )

        content = response.choices[0].message.content
        assert content, "Received empty response from OpenAI API"

        print(f"✅ {model_name} response: {content}")

    except RateLimitError as e:
        pytest.fail(f"❌ {model_name} Rate limit error: {str(e)}")
    except APIError as e:
        pytest.fail(f"❌ {model_name} API error: {str(e)}")
    except Exception as e:
        pytest.fail(f"❌ {model_name} unexpected error: {str(e)}")
