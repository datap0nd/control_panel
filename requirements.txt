import os
import requests

api_key = os.environ["LLM_API_KEY"]
base_url = "https://api.openai.com/v1"  # replace if needed

res = requests.post(
    f"{base_url}/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-oss-120b",
        "messages": [
            {"role": "user", "content": "hey how are you doing"}
        ],
        "max_tokens": 100,
    },
)

print(res.json()["choices"][0]["message"]["content"])
