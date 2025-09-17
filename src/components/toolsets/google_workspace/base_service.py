

import logging
import os
import json
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class BaseGoogleService:
    """
    A base class for Google API services that handles common authentication and service building logic.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.client_secrets_path = client_secrets_path
        self.token_path = token_path
        self.service: Optional[Resource] = None

    def _build_service(self, service_name: str, service_version: str, scopes: List[str]) -> Optional[Resource]:
        """
        Authenticates the user and builds the Google API service object.
        """
        creds = None
        
        current_scopes = []
        if os.path.exists(self.token_path):
            with open(self.token_path, 'r') as token_file:
                try:
                    token_data = json.load(token_file)
                    current_scopes = token_data.get('scopes', [])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse {self.token_path}. Re-authentication may be required.")

        if os.path.exists(self.token_path) and all(s in current_scopes for s in scopes):
            creds = Credentials.from_authorized_user_file(self.token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Check if interactive authentication is allowed by an env var
                if os.getenv('MDS_ALLOW_INTERACTIVE_AUTH') == '1':
                    all_known_scopes = list(set(current_scopes + scopes))
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_path, all_known_scopes)
                    creds = flow.run_local_server(port=8080)
                else:
                    error_message = (
                        "Authentication failed. A valid 'token.json' with all required scopes is missing or expired. "
                        "Please run the 'scripts/authorize_google_services.py' script interactively to generate a valid token."
                    )
                    logger.error(error_message)
                    raise RuntimeError(error_message)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build(service_name, service_version, credentials=creds)
            logger.info(f"Successfully built and authenticated service: {service_name} v{service_version}")
            return self.service
        except Exception as e:
            logger.error(f"An error occurred during service initialization for {service_name}: {e}", exc_info=True)
            return None
