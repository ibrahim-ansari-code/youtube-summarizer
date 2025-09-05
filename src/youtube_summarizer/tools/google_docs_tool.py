from crewai.tools import BaseTool
from typing import Optional, Dict, Any, ClassVar, List
import json
import os
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    import pickle
except ImportError:
    print("Google API libraries not found. Install with: pip install google-api-python-client google-auth-oauthlib")

class GoogleDocsIntegrationTool(BaseTool):
    name: str = "Google Docs Integration Tool"
    description: str = "Creates and uploads summaries to Google Docs with proper formatting."
    
    scopes: ClassVar[List[str]] = ['https://www.googleapis.com/auth/documents', 
                                   'https://www.googleapis.com/auth/drive.file']
    credentials_file: ClassVar[str] = "credentials.json"
    token_file: ClassVar[str] = "token.pickle"
    
    def __init__(self):
        super().__init__()
    
    def _authenticate(self) -> Optional[Any]:
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    return None
                flow = Flow.from_client_secrets_file(self.credentials_file, self.scopes)
                flow.redirect_uri = 'http://localhost:8080/callback'
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def _markdown_to_docs_format(self, markdown_text: str) -> list:
        """Convert markdown to Google Docs API format.
        Note: We insert lines in reverse order at index 1 so the final document
        preserves the original top-to-bottom order.
        """
        requests = []
        lines = markdown_text.split('\n')

        for line in reversed(lines):
            if not line.strip():
                # Preserve blank lines
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': '\n'
                    }
                })
                continue

            if line.startswith('# '):
                text = line[2:].strip()
                # Insert
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': text + '\n'
                    }
                })
                # Style this inserted line
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': len(text) + 1
                        },
                        'textStyle': {
                            'fontSize': {'magnitude': 18, 'unit': 'PT'},
                            'bold': True
                        },
                        'fields': 'fontSize,bold'
                    }
                })
            elif line.startswith('## '):
                text = line[3:].strip()
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': text + '\n'
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': len(text) + 1
                        },
                        'textStyle': {
                            'fontSize': {'magnitude': 14, 'unit': 'PT'},
                            'bold': True
                        },
                        'fields': 'fontSize,bold'
                    }
                })
            elif line.startswith('- ') or line.startswith('* '):
                text = '• ' + line[2:].strip()
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': text + '\n'
                    }
                })
            else:
                # Regular text
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': line + '\n'
                    }
                })

        return requests
    
    def _run(self, summary_content: str, doc_title: str = "YouTube Video Summary", 
             folder_id: Optional[str] = None) -> str:
        """Create a Google Doc with the summary content."""
        try:
            creds = self._authenticate()
            if not creds:
                return "Error: Could not authenticate with Google APIs. Make sure credentials.json is present."
            
            # Build services
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Create new document
            doc = docs_service.documents().create(body={'title': doc_title}).execute()
            doc_id = doc['documentId']
            
            # Format content for Google Docs
            requests = self._markdown_to_docs_format(summary_content)
            
            # Apply formatting to document
            if requests:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Move to specific folder if provided
            if folder_id:
                drive_service.files().update(
                    fileId=doc_id,
                    addParents=folder_id,
                    removeParents='root'
                ).execute()
            
            # Get document URL
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            return f"Successfully created Google Doc: {doc_url}"
            
        except Exception as e:
            return f"Error creating Google Doc: {str(e)}"
