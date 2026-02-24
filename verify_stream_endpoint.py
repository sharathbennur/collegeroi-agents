import requests
import json
import sys

def test_chat_stream():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "Hi, I am planning to go to NYU.",
        "user_id": "test_stream_client_1"
    }
    
    print(f"Connecting to {url}...")
    try:
        # Use stream=True to process the response chunk by chunk
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                return

            print("Stream started:\n")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        # React useChat expects exactly "data: <content>\n\n"
                        # Print it out as it streams in
                        content = decoded_line[6:].replace('\\n', '\n')
                        print(content, end="", flush=True)

            print("\n\nStream finished.")
    except Exception as e:
        print(f"\nFailed to connect or stream: {e}")

if __name__ == "__main__":
    test_chat_stream()
