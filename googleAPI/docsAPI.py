import datetime as dt
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

TOKEN_PATH = "googleAPI/token.json"
CREDENTIALS_PATH = "googleAPI/credentials.json"

def authorize():
    """Handles Google API authorization and token refresh."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"Missing credentials file: {CREDENTIALS_PATH}")

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return creds

def create_google_doc(title):
    """Creates a new Google Document and returns its ID."""
    creds = authorize()
    drive_service = build("drive", "v3", credentials=creds)

    doc_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document"
    }
    doc = drive_service.files().create(body=doc_metadata).execute()
    doc_id = doc.get("id")

    if not doc_id:
        raise Exception("Failed to create Google Doc. No document ID returned.")
    return doc_id

def update_doc_content(doc_id, message):
    """Appends timestamp and message to the end of a Google Doc, ensuring no unwanted text is added."""
    creds = authorize()
    doc_service = build("docs", "v1", credentials=creds)

    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_to_insert = f"{timestamp} - {message}\n"

    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text_to_insert
            }
        }
    ]

    doc_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    doc_url = f"https://docs.google.com/document/d/{doc_id}"
    return {"message": "Content updated", "doc_url": doc_url}

def download_doc_as_pdf(doc_id, saved_folder, title):
    """Downloads a Google Doc as a PDF."""
    creds = authorize()
    
    export_url = f"https://www.googleapis.com/drive/v3/files/{doc_id}/export?mimeType=application/pdf"
    headers = {"Authorization": f"Bearer {creds.token}"}

    response = requests.get(export_url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Unable to download document (status code {response.status_code})")
        return None

    os.makedirs(saved_folder, exist_ok=True)

    file_path = os.path.join(saved_folder, f"{title}.pdf")
    with open(file_path, "wb") as pdf_file:
        pdf_file.write(response.content)

    print(f"Downloaded PDF: {file_path}")
    return {"message": file_path}

cached_doc_id = None

def google_docs_tool(input_text: str, create_only: bool, download: bool):
    global cached_doc_id
    authorize()
    title = "Chat Conversation"

    is_new_doc = False

    if cached_doc_id is None or create_only:
        cached_doc_id = create_google_doc(title)
        is_new_doc = True

    if is_new_doc:
        update_doc_content(cached_doc_id, input_text)

    doc_url = f"https://docs.google.com/document/d/{cached_doc_id}"

    download_info = None
    if download:
        saved_folder = "downloads"
        download_info = download_doc_as_pdf(cached_doc_id, saved_folder, title)

    return {"google_doc_url": doc_url, "download_info": download_info}
