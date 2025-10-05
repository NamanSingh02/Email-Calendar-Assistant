import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# simple in-memory store for demo; you can swap to DB
USER_TOKENS = {}


def client_config():
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "project_id": "email-calendar-assistant",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": [os.getenv("OAUTH_REDIRECT_URI")],
            "javascript_origins": [os.getenv("ALLOWED_ORIGIN")],
        }
    }


def start_auth():
    flow = Flow.from_client_config(client_config(), scopes=SCOPES)
    flow.redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return auth_url, state


def finish_auth(state: str, code: str):
    flow = Flow.from_client_config(client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
    flow.fetch_token(code=code)
    creds = flow.credentials
    USER_TOKENS["demo"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    return True


def get_creds() -> Credentials:
    data = USER_TOKENS.get("demo")
    if not data:
        raise RuntimeError("Not connected.")
    return Credentials(**data)

def is_connected() -> bool:
    return "demo" in USER_TOKENS

def logout():
    USER_TOKENS.pop("demo", None)
