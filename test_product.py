import requests
import json
import webbrowser
import time
from google_auth_oauthlib.flow import InstalledAppFlow
import os

# Base URL for the FastAPI server
BASE_URL = "http://localhost:8000"

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_token():
    # load your downloaded JSON file
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret_desktop.json",  # the file you downloaded
        scopes=SCOPES
    )
    # this spins up a tiny HTTP server on localhost (pick any free port)
    creds = flow.run_local_server(port=8080, open_browser=True)
    return creds.token

def test_chat(token, message, json_data):
    """Test the chat endpoint with a message"""
    print(f"Sending message to chat endpoint: {message}")
    message += json_data
    data = {
        "history": [
            {"role": "user", "content": message}
        ],
        "user_token": token
    }

    try:
        print(f"Using token: {token[:10]}... (truncated)")
        
        response = requests.post(f"{BASE_URL}/chat", json=data)
        if response.status_code == 200:
            print("\nResponse from AI:")
            print(response.json()["message"])
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"An error occurred during chat: {e}")

if __name__ == "__main__":
    canvas_data = json.load(open("canvas.json"))

    print("Starting OAuth authentication flow...")
    # Get authentication token
    token = get_token()
    
    if token:
        print("\nSuccessfully obtained token!")
        print(f"Token: {token[:10]}... (truncated for security)")
        
        # Test with a message that should trigger calendar creation
        test_message = input("\nEnter a message to send (or press Enter for default): ")
        if not test_message:
            test_message = "Create a calendar event based on the following JSON: "
        
        json_data = json.dumps(canvas_data)

        test_chat(token, test_message, json_data)
    else:
        print("Failed to obtain authentication token. Please check the server logs for more details.")