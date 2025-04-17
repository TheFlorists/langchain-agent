import requests
import json
import webbrowser
import time

# Base URL for the FastAPI server
BASE_URL = "http://localhost:8000"

def get_token():
    """Get authentication token using manual entry from browser response"""
    try:
        # Get the authorization URL
        print("Requesting authorization URL...")
        response = requests.get(f"{BASE_URL}/auth")
        
        # Check if response is successful
        if response.status_code != 200:
            print(f"Error: Server returned status code {response.status_code}")
            print(f"Response content: {response.text}")
            return None
            
        # Try to parse JSON response
        try:
            response_data = response.json()
            auth_url = response_data.get("authorization_url")
            if not auth_url:
                print(f"Error: No authorization_url in response: {response_data}")
                return None
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON response: {response.text}")
            return None
            
        print(f"Please authenticate by visiting: {auth_url}")
        print("\nThe browser will open automatically. Please log in and authorize the application.")
        webbrowser.open(auth_url)
        
        print("\nAfter authorizing, you'll see a JSON response in your browser.")
        print("Copy the 'token' value from the JSON response.")
        
        # Get token directly from user input
        token = input("\nPaste the token value from the browser JSON response: ")
        
        if not token:
            print("No token provided.")
            return None
            
        return token
        
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        return None

def test_chat(token, message):
    """Test the chat endpoint with a message"""
    data = {
        "history": [
            {"role": "user", "content": message}
        ],
        "user_token": token
    }
    
    try:
        print(f"Sending message to chat endpoint: {message}")
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
    print("Starting OAuth authentication flow...")
    
    # Get authentication token
    token = get_token()
    
    if token:
        print("\nSuccessfully obtained token!")
        print(f"Token: {token[:10]}... (truncated for security)")
        
        # Test with a message that should trigger calendar creation
        test_message = input("\nEnter a message to send (or press Enter for default): ")
        if not test_message:
            test_message = "Create a calendar event titled 'Product Review' for April 17th, 2025at 2pm for 1 hour"
            print(f"Using default message: '{test_message}'")
        
        test_chat(token, test_message)
    else:
        print("Failed to obtain authentication token. Please check the server logs for more details.")