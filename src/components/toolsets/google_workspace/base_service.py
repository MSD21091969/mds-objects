

import logging
from google.auth import default as google_auth_default
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

        # --- Recommendation: Prioritize Service Account (ADC) ---
        # First, try to get credentials from the environment (Application Default Credentials)
        # This will automatically use GOOGLE_APPLICATION_CREDENTIALS if it's set.
        try:
            creds, project = google_auth_default(scopes=scopes)
            # Add a check to ensure creds are valid, otherwise fall through
            if not (creds and creds.valid):
                creds = None
                logger.info("Application Default Credentials not found or invalid. Falling back to OAuth flow.")
            else:
                 logger.info("Successfully authenticated using Application Default Credentials (Service Account).")
        except Exception as e:
            logger.info(f"Could not use Application Default Credentials: {e}. Falling back to OAuth flow.")
            creds = None
        # --- End Recommendation ---

        # Fallback to the original OAuth 2.0 flow if ADC fails
        if not creds: # Only run this block if ADC failed
            logger.info("Attempting authentication using local OAuth 2.0 flow (token.json / client_secrets.json).")
            if os.path.exists(self.token_path):
                # Check if existing token has all the required scopes
                with open(self.token_path, 'r') as token:
                    token_data = json.load(token)
                    existing_scopes = token_data.get('scopes', [])
                if all(s in existing_scopes for s in scopes):
                    creds = Credentials.from_authorized_user_file(self.token_path, scopes)
                else:
                    # Scopes have changed, force re-authentication
                    creds = None

            # If there are no (valid) credentials, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Check if interactive authentication is allowed by an env var
                    if os.getenv('MDS_ALLOW_INTERACTIVE_AUTH') == '1':
                        # Combine all known scopes to avoid re-auth for every tool
                        all_known_scopes = list(set(existing_scopes + scopes))
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secrets_path, all_known_scopes)
                        creds = flow.run_local_server(port=8080)
                    else:
                        error_message = (
                            "Authentication failed. No valid credentials found (neither ADC nor token.json). "
                            "To use OAuth, set MDS_ALLOW_INTERACTIVE_AUTH=1. "
                            "To use a service account, ensure GOOGLE_APPLICATION_CREDENTIALS is set correctly."
                        )
                        logger.error(error_message)
                        raise RuntimeError(error_message)

                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
        
        try:
            self.service = build(service_name, service_version, credentials=creds)
            logger.info(f"Successfully built service: {service_name} v{service_version}")
            return self.service
        except Exception as e:
            logger.error(f"An error occurred during service initialization for {service_name}: {e}", exc_info=True)
            return None
