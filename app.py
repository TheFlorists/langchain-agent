from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

app = FastAPI()
load_dotenv()

# API Keys and credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")

# OAuth setup
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token",
)

# Gemini client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Models
class ChatTurn(BaseModel):
    role: str  # user OR assistant
    content: str

class ChatRequest(BaseModel):
    history: List[ChatTurn]
    user_token: Optional[str] = None  # OAuth token for the user

class CalendarEvent(BaseModel):
    summary: str
    start_time: str  # ISO format datetime
    end_time: str  # ISO format datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

# Format chat history for Gemini API
def format_message(turn: ChatTurn) -> dict:
    return {
        "role": turn.role,
        "parts": [{"text": turn.content}]
    }

# OAuth flow setup
def get_oauth_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

# Calendar API client setup
def get_calendar_service(credentials):
    return build("calendar", "v3", credentials=credentials)

# Tool functions
def say_hello_world():
    """Say hello world back to the user if the user asks for it
    Args:
        no args
    Returns:
        a string saying hello world
    """
    return "hello world tool call TEST"

def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = None,
    location: str = None,
    attendees: List[str] = None,
    user_token: str = None,
) -> str:
    """Create a new event in the user's Google Calendar.
    
    Args:
        summary: Title of the event
        start_time: Start time (ISO format: YYYY-MM-DDTHH:MM:SS±HH:MM)
        end_time: End time (ISO format: YYYY-MM-DDTHH:MM:SS±HH:MM)
        description: Description of the event
        location: Location of the event
        attendees: List of email addresses for attendees
        user_token: OAuth token for the user
    
    Returns:
        A confirmation message with the event details and link
    """
    if not user_token:
        return "Error: User authentication token is required to create calendar events."
    
    try:
        # Create credentials from the token
        credentials = Credentials(user_token)
        service = build("calendar", "v3", credentials=credentials)
        
        # Format event data
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Los_Angeles',  # You might want to make this configurable
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Los_Angeles',
            },
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Insert the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        # Return success message with link to event
        return f"Event created successfully! View it at: {created_event.get('htmlLink')}"
    
    except Exception as e:
        return f"Error creating calendar event: {str(e)}"

# Routes
@app.get("/auth")
async def auth_redirect():
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    # Create the flow instance with explicit redirect_uri
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
        redirect_uri=redirect_uri  # Set it here only, not in authorization_url
    )
    
    # Generate the authorization URL WITHOUT additional redirect_uri parameter
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
        # Remove redirect_uri from here since it's already set in the Flow constructor
    )
    
    return {"authorization_url": authorization_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
        redirect_uri=redirect_uri
    )
    
    # Fetch token WITHOUT additional redirect_uri
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "scopes": credentials.scopes,
    }

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    if not chat_request.history:
        raise HTTPException(status_code=400, detail="Chat history is empty.")
    
    formatted_history = [format_message(turn) for turn in chat_request.history]
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Set up tools
    config = types.GenerateContentConfig(
        tools=[
            {
                "function_declarations": [
                    {
                        "name": "create_calendar_event",
                        "description": "Create a new event in Google Calendar",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Title of the event"
                                },
                                "start_time": {
                                    "type": "string", 
                                    "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                },
                                "end_time": {
                                    "type": "string",
                                    "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Optional description for the event"
                                },
                                "location": {
                                    "type": "string",
                                    "description": "Optional location for the event"
                                },
                                "attendees": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional list of email addresses for attendees"
                                }
                            },
                            "required": ["title", "start_time", "end_time"]
                        }
                    },
                    {
                        "name": "say_hello_world",
                        "description": "Say hello world back to the user if the user asks for it",
                        "parameters": {"type": "object", "properties": {}}
                    }
                ]
            }
        ]
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=formatted_history,
            config=config
        )
        
        # Handle function calling if present
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        if function_call:
                            if function_call.name == "create_calendar_event":
                                # Extract arguments - handle both string and dict cases
                                args = function_call.args
                                if isinstance(args, str):
                                    # Parse JSON string to dictionary
                                    args = json.loads(args)
                                # If it's already a dict, use it directly
                                
                                # Call the calendar creation function
                                result = create_calendar_event(
                                    summary=args.get("title"),
                                    start_time=args.get("start_time"),
                                    end_time=args.get("end_time"),
                                    description=args.get("description"),
                                    location=args.get("location"),
                                    attendees=args.get("attendees"),
                                    user_token=chat_request.user_token
                                )
                                
                                # Return result with the model's response
                                return {"message": f"{response.text}\n\nCalendar Result: {result}"}
                            
                            elif function_call.name == "say_hello_world":
                                result = say_hello_world()
                                return {"message": f"{response.text}\n\nTool Result: {result}"}
        
        # If no function call, return the standard response
        return {"message": response.text}
        
    except Exception as e:
        # Add more detailed error logging
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")