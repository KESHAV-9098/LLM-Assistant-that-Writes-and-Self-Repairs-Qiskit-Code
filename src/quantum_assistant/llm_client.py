import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:3b"
TIMEOUT = 360


def generate_response(prompt):
    """
    Send a prompt to the local Ollama model
    and return its generated response.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running."
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama request timed out. Try again."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Ollama request failed: {error}")

    except (KeyError, ValueError):
        raise RuntimeError("Invalid response received from Ollama.")
