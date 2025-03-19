from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from googleAPI import docsAPI

app = FastAPI()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# format for a message
class ChatTurn(BaseModel):
    role: str # user OR assistant
    content: str

### REQUIRED FORMAT FOR SENDING REQUEST
class ChatRequest(BaseModel):
    history: List[ChatTurn]
    create_google_doc: Optional[bool] = False  # Create empty Google Doc
    save_doc: Optional[bool] = False  # Save content to Google Doc
    
# Format chat history for Gemini api
def format_message(turn: ChatTurn) -> dict:
    return {
        "role": turn.role,
        "parts": [
            {
                "text": turn.content,
            }
        ]
    }

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    if not chat_request.history:
        raise HTTPException(status_code=400, detail="Chat history is empty.")

    formatted_history = [format_message(turn) for turn in chat_request.history]

    client = genai.Client(api_key=GEMINI_API_KEY)

    # set up tools
    config = types.GenerateContentConfig(
        tools=[
            say_hello_world,
            docsAPI.google_docs_tool
        ])

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=formatted_history,
            config=config)
        
        response_text = response.text
        
        ### GOOGLE DOCS
        doc_url = None
        download_info = None

        if chat_request.create_google_doc or chat_request.save_doc:
            
            doc_result = docsAPI.google_docs_tool(
                input_text=response_text,
                create_only=chat_request.create_google_doc,
                save_doc=chat_request.save_doc
            )
            doc_url = doc_result["google_doc_url"]
            download_info = doc_result["download_info"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")

    return {
        "message": response_text,
        "google_doc_url": doc_url,
        "download_info": download_info
    }



def say_hello_world():
    """Say hello world back to the user if the user asks for it

    Args:
        no args

    Returns:
        a string saying hello world
    """
    return 'hello world tool call TEST'

