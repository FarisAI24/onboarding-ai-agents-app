"""
External Calendar Integration - Future Implementation

This module contains commented-out code for integrating with external calendar
providers (Google Calendar and Microsoft Outlook/365). 

IMPORTANT: This code is NOT active and requires additional setup:

Prerequisites:
1. Install required packages:
   - pip install google-auth google-auth-oauthlib google-api-python-client
   - pip install msal requests

2. Configure OAuth credentials:
   Google Calendar:
   - Go to Google Cloud Console (https://console.cloud.google.com)
   - Create a project and enable Google Calendar API
   - Create OAuth 2.0 credentials (Web application)
   - Set redirect URI to: http://localhost:8000/api/v1/calendar/oauth/google/callback
   
   Microsoft Calendar:
   - Go to Azure Portal (https://portal.azure.com)
   - Register an application in Azure Active Directory
   - Add API permissions for Microsoft Graph (Calendars.ReadWrite, User.Read)
   - Set redirect URI to: http://localhost:8000/api/v1/calendar/oauth/microsoft/callback

3. Set environment variables:
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/google/callback
   
   MICROSOFT_CLIENT_ID=your_microsoft_client_id
   MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
   MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/microsoft/callback
   MICROSOFT_AUTHORITY=https://login.microsoftonline.com/common

4. Add OAuthToken model to database/models.py (see below)

5. Uncomment and integrate the code below

Usage:
    To enable, uncomment the code sections below and the corresponding routes
    in feature_routes.py, then add the OAuthToken model to your database.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']
# MICROSOFT_SCOPES = ['Calendars.ReadWrite', 'User.Read']
# GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'


# =============================================================================
# Database Model for OAuth Tokens
# =============================================================================
# 
# Add this to app/database/models.py:
# 
# class OAuthToken(Base):
#     """Store OAuth tokens for external calendar providers."""
#     __tablename__ = "oauth_tokens"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     provider = Column(String(50), nullable=False)  # 'google' or 'microsoft'
#     access_token = Column(Text, nullable=False)
#     refresh_token = Column(Text)
#     token_type = Column(String(50))
#     expires_at = Column(DateTime)
#     scope = Column(Text)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     
#     user = relationship("User", back_populates="oauth_tokens")
#     
#     __table_args__ = (
#         UniqueConstraint('user_id', 'provider', name='unique_user_provider'),
#     )
# 
# Also add to CalendarEvent model:
#     external_google_id = Column(String(255), nullable=True)
#     external_microsoft_id = Column(String(255), nullable=True)


# =============================================================================
# Google Calendar Provider
# =============================================================================

# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import Flow
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from sqlalchemy.orm import Session
# 
# class GoogleCalendarProvider:
#     """Google Calendar OAuth integration.
#     
#     This class handles OAuth flow and API interactions with Google Calendar.
#     
#     Example usage:
#         provider = GoogleCalendarProvider(db)
#         
#         # Step 1: Get authorization URL and redirect user
#         auth_url = provider.get_authorization_url(user_id)
#         
#         # Step 2: Handle callback (after user authorizes)
#         success = provider.handle_oauth_callback(code, user_id)
#         
#         # Step 3: Create/manage events
#         google_event_id = provider.create_event(user_id, event)
#     """
#     
#     def __init__(self, db: Session):
#         self.db = db
#         self.client_id = os.getenv('GOOGLE_CLIENT_ID')
#         self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
#         self.redirect_uri = os.getenv(
#             'GOOGLE_REDIRECT_URI', 
#             'http://localhost:8000/api/v1/calendar/oauth/google/callback'
#         )
#         
#         if not self.client_id or not self.client_secret:
#             logger.warning("Google Calendar credentials not configured")
#     
#     def get_authorization_url(self, user_id: int) -> str:
#         """Generate OAuth authorization URL for Google Calendar.
#         
#         Args:
#             user_id: The internal user ID to associate with this OAuth flow
#             
#         Returns:
#             Authorization URL to redirect the user to
#         """
#         flow = Flow.from_client_config(
#             {
#                 "web": {
#                     "client_id": self.client_id,
#                     "client_secret": self.client_secret,
#                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#                     "token_uri": "https://oauth2.googleapis.com/token",
#                 }
#             },
#             scopes=GOOGLE_SCOPES,
#             redirect_uri=self.redirect_uri
#         )
#         
#         authorization_url, state = flow.authorization_url(
#             access_type='offline',        # Get refresh token
#             include_granted_scopes='true',
#             prompt='consent',             # Force consent to get refresh token
#             state=str(user_id)            # Pass user_id in state for callback
#         )
#         
#         return authorization_url
#     
#     def handle_oauth_callback(self, code: str, user_id: int) -> bool:
#         """Handle OAuth callback and store tokens.
#         
#         Args:
#             code: Authorization code from Google
#             user_id: User ID from state parameter
#             
#         Returns:
#             True if successful, False otherwise
#         """
#         try:
#             flow = Flow.from_client_config(
#                 {
#                     "web": {
#                         "client_id": self.client_id,
#                         "client_secret": self.client_secret,
#                         "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#                         "token_uri": "https://oauth2.googleapis.com/token",
#                     }
#                 },
#                 scopes=GOOGLE_SCOPES,
#                 redirect_uri=self.redirect_uri
#             )
#             
#             flow.fetch_token(code=code)
#             credentials = flow.credentials
#             
#             # Store tokens in database
#             self._store_tokens(user_id, 'google', {
#                 'access_token': credentials.token,
#                 'refresh_token': credentials.refresh_token,
#                 'token_type': 'Bearer',
#                 'expires_at': credentials.expiry,
#                 'scope': ' '.join(credentials.scopes or [])
#             })
#             
#             logger.info(f"Google Calendar connected for user {user_id}")
#             return True
#             
#         except Exception as e:
#             logger.error(f"Google OAuth callback failed: {e}")
#             return False
#     
#     def _store_tokens(self, user_id: int, provider: str, tokens: dict):
#         """Store or update OAuth tokens in database."""
#         from app.database.models import OAuthToken
#         
#         existing = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == provider
#         ).first()
#         
#         if existing:
#             existing.access_token = tokens['access_token']
#             existing.refresh_token = tokens.get('refresh_token') or existing.refresh_token
#             existing.expires_at = tokens.get('expires_at')
#             existing.scope = tokens.get('scope')
#             existing.updated_at = datetime.utcnow()
#         else:
#             new_token = OAuthToken(
#                 user_id=user_id,
#                 provider=provider,
#                 access_token=tokens['access_token'],
#                 refresh_token=tokens.get('refresh_token'),
#                 token_type=tokens.get('token_type', 'Bearer'),
#                 expires_at=tokens.get('expires_at'),
#                 scope=tokens.get('scope')
#             )
#             self.db.add(new_token)
#         
#         self.db.commit()
#     
#     def _load_credentials(self, user_id: int) -> Optional[Credentials]:
#         """Load credentials from database."""
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'google'
#         ).first()
#         
#         if not token:
#             return None
#         
#         return Credentials(
#             token=token.access_token,
#             refresh_token=token.refresh_token,
#             token_uri="https://oauth2.googleapis.com/token",
#             client_id=self.client_id,
#             client_secret=self.client_secret,
#             scopes=GOOGLE_SCOPES
#         )
#     
#     def get_service(self, user_id: int):
#         """Get authenticated Google Calendar service.
#         
#         Args:
#             user_id: User ID to get service for
#             
#         Returns:
#             Google Calendar API service object
#             
#         Raises:
#             ValueError: If user not connected to Google Calendar
#         """
#         credentials = self._load_credentials(user_id)
#         if not credentials:
#             raise ValueError("User not connected to Google Calendar")
#         
#         # Refresh token if expired
#         if credentials.expired and credentials.refresh_token:
#             credentials.refresh(Request())
#             self._store_tokens(user_id, 'google', {
#                 'access_token': credentials.token,
#                 'refresh_token': credentials.refresh_token,
#                 'expires_at': credentials.expiry
#             })
#         
#         return build('calendar', 'v3', credentials=credentials)
#     
#     def create_event(self, user_id: int, event) -> str:
#         """Create event in Google Calendar.
#         
#         Args:
#             user_id: User ID
#             event: CalendarEvent object
#             
#         Returns:
#             Google Calendar event ID
#         """
#         service = self.get_service(user_id)
#         
#         google_event = {
#             'summary': event.title,
#             'description': event.description or '',
#             'start': {
#                 'dateTime': event.start_time.isoformat(),
#                 'timeZone': 'UTC',
#             },
#             'end': {
#                 'dateTime': (event.end_time or event.start_time + timedelta(hours=1)).isoformat(),
#                 'timeZone': 'UTC',
#             },
#             'reminders': {
#                 'useDefault': False,
#                 'overrides': [
#                     {'method': 'popup', 'minutes': event.reminder_minutes},
#                     {'method': 'email', 'minutes': event.reminder_minutes},
#                 ],
#             },
#         }
#         
#         try:
#             result = service.events().insert(
#                 calendarId='primary', 
#                 body=google_event
#             ).execute()
#             
#             logger.info(f"Created Google Calendar event: {result.get('id')}")
#             return result.get('id')
#             
#         except HttpError as e:
#             logger.error(f"Failed to create Google Calendar event: {e}")
#             raise
#     
#     def update_event(self, user_id: int, google_event_id: str, event) -> bool:
#         """Update event in Google Calendar."""
#         service = self.get_service(user_id)
#         
#         google_event = {
#             'summary': event.title,
#             'description': event.description or '',
#             'start': {
#                 'dateTime': event.start_time.isoformat(),
#                 'timeZone': 'UTC',
#             },
#             'end': {
#                 'dateTime': (event.end_time or event.start_time + timedelta(hours=1)).isoformat(),
#                 'timeZone': 'UTC',
#             },
#         }
#         
#         try:
#             service.events().update(
#                 calendarId='primary',
#                 eventId=google_event_id,
#                 body=google_event
#             ).execute()
#             return True
#         except HttpError as e:
#             logger.error(f"Failed to update Google Calendar event: {e}")
#             return False
#     
#     def delete_event(self, user_id: int, google_event_id: str) -> bool:
#         """Delete event from Google Calendar."""
#         service = self.get_service(user_id)
#         
#         try:
#             service.events().delete(
#                 calendarId='primary', 
#                 eventId=google_event_id
#             ).execute()
#             return True
#         except HttpError as e:
#             logger.error(f"Failed to delete Google Calendar event: {e}")
#             return False
#     
#     def sync_from_google(self, user_id: int, days_ahead: int = 30) -> List[Dict]:
#         """Sync events from Google Calendar to local database.
#         
#         Args:
#             user_id: User ID
#             days_ahead: Number of days ahead to sync
#             
#         Returns:
#             List of synced events
#         """
#         service = self.get_service(user_id)
#         
#         now = datetime.utcnow()
#         time_min = now.isoformat() + 'Z'
#         time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
#         
#         events_result = service.events().list(
#             calendarId='primary',
#             timeMin=time_min,
#             timeMax=time_max,
#             maxResults=100,
#             singleEvents=True,
#             orderBy='startTime'
#         ).execute()
#         
#         return events_result.get('items', [])
#     
#     def is_connected(self, user_id: int) -> bool:
#         """Check if user has connected Google Calendar."""
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'google'
#         ).first()
#         
#         return token is not None
#     
#     def disconnect(self, user_id: int) -> bool:
#         """Disconnect Google Calendar for user."""
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'google'
#         ).first()
#         
#         if token:
#             self.db.delete(token)
#             self.db.commit()
#             logger.info(f"Google Calendar disconnected for user {user_id}")
#             return True
#         return False


# =============================================================================
# Microsoft Outlook/Graph Calendar Provider
# =============================================================================

# import msal
# import requests
# from sqlalchemy.orm import Session
# 
# class MicrosoftCalendarProvider:
#     """Microsoft Outlook/Graph Calendar OAuth integration.
#     
#     This class handles OAuth flow and API interactions with Microsoft Graph API
#     for Outlook Calendar integration.
#     
#     Example usage:
#         provider = MicrosoftCalendarProvider(db)
#         
#         # Step 1: Get authorization URL and redirect user
#         auth_url = provider.get_authorization_url(user_id)
#         
#         # Step 2: Handle callback (after user authorizes)
#         success = provider.handle_oauth_callback(code, user_id)
#         
#         # Step 3: Create/manage events
#         outlook_event_id = provider.create_event(user_id, event)
#     """
#     
#     def __init__(self, db: Session):
#         self.db = db
#         self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
#         self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
#         self.redirect_uri = os.getenv(
#             'MICROSOFT_REDIRECT_URI',
#             'http://localhost:8000/api/v1/calendar/oauth/microsoft/callback'
#         )
#         self.authority = os.getenv(
#             'MICROSOFT_AUTHORITY',
#             'https://login.microsoftonline.com/common'
#         )
#         
#         if not self.client_id or not self.client_secret:
#             logger.warning("Microsoft Calendar credentials not configured")
#             self.app = None
#         else:
#             self.app = msal.ConfidentialClientApplication(
#                 self.client_id,
#                 authority=self.authority,
#                 client_credential=self.client_secret,
#             )
#     
#     def get_authorization_url(self, user_id: int) -> str:
#         """Generate OAuth authorization URL for Microsoft Calendar.
#         
#         Args:
#             user_id: The internal user ID to associate with this OAuth flow
#             
#         Returns:
#             Authorization URL to redirect the user to
#         """
#         if not self.app:
#             raise ValueError("Microsoft Calendar not configured")
#         
#         auth_url = self.app.get_authorization_request_url(
#             MICROSOFT_SCOPES,
#             redirect_uri=self.redirect_uri,
#             state=str(user_id),
#             prompt='consent'  # Force consent to ensure refresh token
#         )
#         
#         return auth_url
#     
#     def handle_oauth_callback(self, code: str, user_id: int) -> bool:
#         """Handle OAuth callback and store tokens.
#         
#         Args:
#             code: Authorization code from Microsoft
#             user_id: User ID from state parameter
#             
#         Returns:
#             True if successful, False otherwise
#         """
#         if not self.app:
#             return False
#         
#         try:
#             result = self.app.acquire_token_by_authorization_code(
#                 code,
#                 scopes=MICROSOFT_SCOPES,
#                 redirect_uri=self.redirect_uri
#             )
#             
#             if 'access_token' in result:
#                 # Calculate expiration time
#                 expires_in = result.get('expires_in', 3600)
#                 expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
#                 
#                 # Store tokens in database
#                 self._store_tokens(user_id, 'microsoft', {
#                     'access_token': result['access_token'],
#                     'refresh_token': result.get('refresh_token'),
#                     'token_type': result.get('token_type', 'Bearer'),
#                     'expires_at': expires_at,
#                     'scope': ' '.join(result.get('scope', []))
#                 })
#                 
#                 logger.info(f"Microsoft Calendar connected for user {user_id}")
#                 return True
#             else:
#                 logger.error(f"Microsoft OAuth failed: {result.get('error_description')}")
#                 return False
#                 
#         except Exception as e:
#             logger.error(f"Microsoft OAuth callback failed: {e}")
#             return False
#     
#     def _store_tokens(self, user_id: int, provider: str, tokens: dict):
#         """Store or update OAuth tokens in database."""
#         from app.database.models import OAuthToken
#         
#         existing = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == provider
#         ).first()
#         
#         if existing:
#             existing.access_token = tokens['access_token']
#             existing.refresh_token = tokens.get('refresh_token') or existing.refresh_token
#             existing.expires_at = tokens.get('expires_at')
#             existing.scope = tokens.get('scope')
#             existing.updated_at = datetime.utcnow()
#         else:
#             new_token = OAuthToken(
#                 user_id=user_id,
#                 provider=provider,
#                 access_token=tokens['access_token'],
#                 refresh_token=tokens.get('refresh_token'),
#                 token_type=tokens.get('token_type', 'Bearer'),
#                 expires_at=tokens.get('expires_at'),
#                 scope=tokens.get('scope')
#             )
#             self.db.add(new_token)
#         
#         self.db.commit()
#     
#     def get_access_token(self, user_id: int) -> str:
#         """Get valid access token, refreshing if necessary.
#         
#         Args:
#             user_id: User ID
#             
#         Returns:
#             Valid access token
#             
#         Raises:
#             ValueError: If user not connected or token refresh fails
#         """
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'microsoft'
#         ).first()
#         
#         if not token:
#             raise ValueError("User not connected to Microsoft Calendar")
#         
#         # Check if token is expired
#         if token.expires_at and token.expires_at < datetime.utcnow():
#             # Refresh the token
#             if not token.refresh_token:
#                 raise ValueError("No refresh token available")
#             
#             result = self.app.acquire_token_by_refresh_token(
#                 token.refresh_token,
#                 scopes=MICROSOFT_SCOPES
#             )
#             
#             if 'access_token' in result:
#                 expires_in = result.get('expires_in', 3600)
#                 expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
#                 
#                 self._store_tokens(user_id, 'microsoft', {
#                     'access_token': result['access_token'],
#                     'refresh_token': result.get('refresh_token'),
#                     'expires_at': expires_at
#                 })
#                 
#                 return result['access_token']
#             else:
#                 raise ValueError("Token refresh failed")
#         
#         return token.access_token
#     
#     def create_event(self, user_id: int, event) -> str:
#         """Create event in Microsoft Calendar.
#         
#         Args:
#             user_id: User ID
#             event: CalendarEvent object
#             
#         Returns:
#             Outlook event ID
#         """
#         access_token = self.get_access_token(user_id)
#         
#         outlook_event = {
#             'subject': event.title,
#             'body': {
#                 'contentType': 'text',
#                 'content': event.description or ''
#             },
#             'start': {
#                 'dateTime': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
#                 'timeZone': 'UTC'
#             },
#             'end': {
#                 'dateTime': (event.end_time or event.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
#                 'timeZone': 'UTC'
#             },
#             'reminderMinutesBeforeStart': event.reminder_minutes,
#             'isReminderOn': True
#         }
#         
#         response = requests.post(
#             f"{GRAPH_API_ENDPOINT}/me/calendar/events",
#             headers={
#                 'Authorization': f'Bearer {access_token}',
#                 'Content-Type': 'application/json'
#             },
#             json=outlook_event
#         )
#         
#         if response.status_code == 201:
#             event_id = response.json().get('id')
#             logger.info(f"Created Outlook event: {event_id}")
#             return event_id
#         else:
#             logger.error(f"Failed to create Outlook event: {response.text}")
#             raise Exception(f"Failed to create event: {response.status_code}")
#     
#     def update_event(self, user_id: int, outlook_event_id: str, event) -> bool:
#         """Update event in Microsoft Calendar."""
#         access_token = self.get_access_token(user_id)
#         
#         outlook_event = {
#             'subject': event.title,
#             'body': {
#                 'contentType': 'text',
#                 'content': event.description or ''
#             },
#             'start': {
#                 'dateTime': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
#                 'timeZone': 'UTC'
#             },
#             'end': {
#                 'dateTime': (event.end_time or event.start_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
#                 'timeZone': 'UTC'
#             },
#         }
#         
#         response = requests.patch(
#             f"{GRAPH_API_ENDPOINT}/me/calendar/events/{outlook_event_id}",
#             headers={
#                 'Authorization': f'Bearer {access_token}',
#                 'Content-Type': 'application/json'
#             },
#             json=outlook_event
#         )
#         
#         return response.status_code == 200
#     
#     def delete_event(self, user_id: int, outlook_event_id: str) -> bool:
#         """Delete event from Microsoft Calendar."""
#         access_token = self.get_access_token(user_id)
#         
#         response = requests.delete(
#             f"{GRAPH_API_ENDPOINT}/me/calendar/events/{outlook_event_id}",
#             headers={'Authorization': f'Bearer {access_token}'}
#         )
#         
#         return response.status_code == 204
#     
#     def sync_from_outlook(self, user_id: int, days_ahead: int = 30) -> List[Dict]:
#         """Sync events from Microsoft Calendar to local database.
#         
#         Args:
#             user_id: User ID
#             days_ahead: Number of days ahead to sync
#             
#         Returns:
#             List of synced events
#         """
#         access_token = self.get_access_token(user_id)
#         
#         now = datetime.utcnow()
#         time_min = now.strftime('%Y-%m-%dT%H:%M:%SZ')
#         time_max = (now + timedelta(days=days_ahead)).strftime('%Y-%m-%dT%H:%M:%SZ')
#         
#         response = requests.get(
#             f"{GRAPH_API_ENDPOINT}/me/calendar/events",
#             headers={'Authorization': f'Bearer {access_token}'},
#             params={
#                 '$filter': f"start/dateTime ge '{time_min}' and start/dateTime le '{time_max}'",
#                 '$top': 100,
#                 '$orderby': 'start/dateTime'
#             }
#         )
#         
#         if response.status_code == 200:
#             return response.json().get('value', [])
#         return []
#     
#     def is_connected(self, user_id: int) -> bool:
#         """Check if user has connected Microsoft Calendar."""
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'microsoft'
#         ).first()
#         
#         return token is not None
#     
#     def disconnect(self, user_id: int) -> bool:
#         """Disconnect Microsoft Calendar for user."""
#         from app.database.models import OAuthToken
#         
#         token = self.db.query(OAuthToken).filter(
#             OAuthToken.user_id == user_id,
#             OAuthToken.provider == 'microsoft'
#         ).first()
#         
#         if token:
#             self.db.delete(token)
#             self.db.commit()
#             logger.info(f"Microsoft Calendar disconnected for user {user_id}")
#             return True
#         return False


# =============================================================================
# API Routes (Add to feature_routes.py when enabling)
# =============================================================================
# 
# from fastapi import APIRouter, Depends
# from fastapi.responses import RedirectResponse
# from sqlalchemy.orm import Session
# 
# # Google Calendar OAuth Routes
# 
# @router.get("/calendar/oauth/google/authorize", tags=["Calendar OAuth"])
# async def google_calendar_authorize(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Get Google Calendar authorization URL.
#     
#     Redirect the user to this URL to start the OAuth flow.
#     """
#     provider = GoogleCalendarProvider(db)
#     auth_url = provider.get_authorization_url(current_user.id)
#     return {"authorization_url": auth_url}
# 
# 
# @router.get("/calendar/oauth/google/callback", tags=["Calendar OAuth"])
# async def google_calendar_callback(
#     code: str,
#     state: str,
#     db: Session = Depends(get_db)
# ):
#     """Handle Google Calendar OAuth callback.
#     
#     This endpoint is called by Google after user authorization.
#     """
#     user_id = int(state)
#     provider = GoogleCalendarProvider(db)
#     success = provider.handle_oauth_callback(code, user_id)
#     
#     if success:
#         return RedirectResponse(url="/calendar?connected=google")
#     return RedirectResponse(url="/calendar?error=google_oauth_failed")
# 
# 
# @router.delete("/calendar/oauth/google/disconnect", tags=["Calendar OAuth"])
# async def google_calendar_disconnect(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Disconnect Google Calendar."""
#     provider = GoogleCalendarProvider(db)
#     success = provider.disconnect(current_user.id)
#     return {"disconnected": success}
# 
# 
# @router.get("/calendar/oauth/google/status", tags=["Calendar OAuth"])
# async def google_calendar_status(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Check Google Calendar connection status."""
#     provider = GoogleCalendarProvider(db)
#     connected = provider.is_connected(current_user.id)
#     return {"connected": connected, "provider": "google"}
# 
# 
# # Microsoft Calendar OAuth Routes
# 
# @router.get("/calendar/oauth/microsoft/authorize", tags=["Calendar OAuth"])
# async def microsoft_calendar_authorize(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Get Microsoft Calendar authorization URL.
#     
#     Redirect the user to this URL to start the OAuth flow.
#     """
#     provider = MicrosoftCalendarProvider(db)
#     auth_url = provider.get_authorization_url(current_user.id)
#     return {"authorization_url": auth_url}
# 
# 
# @router.get("/calendar/oauth/microsoft/callback", tags=["Calendar OAuth"])
# async def microsoft_calendar_callback(
#     code: str,
#     state: str,
#     db: Session = Depends(get_db)
# ):
#     """Handle Microsoft Calendar OAuth callback.
#     
#     This endpoint is called by Microsoft after user authorization.
#     """
#     user_id = int(state)
#     provider = MicrosoftCalendarProvider(db)
#     success = provider.handle_oauth_callback(code, user_id)
#     
#     if success:
#         return RedirectResponse(url="/calendar?connected=microsoft")
#     return RedirectResponse(url="/calendar?error=microsoft_oauth_failed")
# 
# 
# @router.delete("/calendar/oauth/microsoft/disconnect", tags=["Calendar OAuth"])
# async def microsoft_calendar_disconnect(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Disconnect Microsoft Calendar."""
#     provider = MicrosoftCalendarProvider(db)
#     success = provider.disconnect(current_user.id)
#     return {"disconnected": success}
# 
# 
# @router.get("/calendar/oauth/microsoft/status", tags=["Calendar OAuth"])
# async def microsoft_calendar_status(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Check Microsoft Calendar connection status."""
#     provider = MicrosoftCalendarProvider(db)
#     connected = provider.is_connected(current_user.id)
#     return {"connected": connected, "provider": "microsoft"}
# 
# 
# # Sync Routes
# 
# @router.post("/calendar/sync/google", tags=["Calendar Sync"])
# async def sync_to_google_calendar(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Sync local events to Google Calendar."""
#     provider = GoogleCalendarProvider(db)
#     service = CalendarService(db)
#     
#     if not provider.is_connected(current_user.id):
#         raise HTTPException(status_code=400, detail="Google Calendar not connected")
#     
#     events = service.get_events(current_user.id, include_past=False)
#     synced = 0
#     errors = []
#     
#     for event in events:
#         if not event.external_google_id:
#             try:
#                 google_id = provider.create_event(current_user.id, event)
#                 service.update_event(event.id, external_google_id=google_id)
#                 synced += 1
#             except Exception as e:
#                 errors.append({"event_id": event.id, "error": str(e)})
#     
#     return {"synced_count": synced, "errors": errors}
# 
# 
# @router.post("/calendar/sync/microsoft", tags=["Calendar Sync"])
# async def sync_to_microsoft_calendar(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Sync local events to Microsoft Calendar."""
#     provider = MicrosoftCalendarProvider(db)
#     service = CalendarService(db)
#     
#     if not provider.is_connected(current_user.id):
#         raise HTTPException(status_code=400, detail="Microsoft Calendar not connected")
#     
#     events = service.get_events(current_user.id, include_past=False)
#     synced = 0
#     errors = []
#     
#     for event in events:
#         if not event.external_microsoft_id:
#             try:
#                 microsoft_id = provider.create_event(current_user.id, event)
#                 service.update_event(event.id, external_microsoft_id=microsoft_id)
#                 synced += 1
#             except Exception as e:
#                 errors.append({"event_id": event.id, "error": str(e)})
#     
#     return {"synced_count": synced, "errors": errors}
# 
# 
# @router.get("/calendar/connections", tags=["Calendar OAuth"])
# async def get_calendar_connections(
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all calendar connection statuses."""
#     google = GoogleCalendarProvider(db)
#     microsoft = MicrosoftCalendarProvider(db)
#     
#     return {
#         "google": {
#             "connected": google.is_connected(current_user.id),
#             "configured": bool(os.getenv('GOOGLE_CLIENT_ID'))
#         },
#         "microsoft": {
#             "connected": microsoft.is_connected(current_user.id),
#             "configured": bool(os.getenv('MICROSOFT_CLIENT_ID'))
#         }
#     }


# =============================================================================
# Frontend Integration (Add to CalendarView.tsx when enabling)
# =============================================================================
# 
# // Add to CalendarView component state:
# const [calendarConnections, setCalendarConnections] = useState({
#   google: { connected: false, configured: false },
#   microsoft: { connected: false, configured: false }
# });
# 
# // Add useEffect to check connections:
# useEffect(() => {
#   const checkConnections = async () => {
#     try {
#       const connections = await api.request('/calendar/connections');
#       setCalendarConnections(connections);
#     } catch (error) {
#       console.error('Failed to check calendar connections:', error);
#     }
#   };
#   checkConnections();
# }, []);
# 
# // Add connection buttons to the UI:
# <div className="flex gap-2">
#   {calendarConnections.google.configured && (
#     calendarConnections.google.connected ? (
#       <button onClick={handleDisconnectGoogle} className="...">
#         Disconnect Google
#       </button>
#     ) : (
#       <button onClick={handleConnectGoogle} className="...">
#         <GoogleIcon /> Connect Google Calendar
#       </button>
#     )
#   )}
#   
#   {calendarConnections.microsoft.configured && (
#     calendarConnections.microsoft.connected ? (
#       <button onClick={handleDisconnectMicrosoft} className="...">
#         Disconnect Outlook
#       </button>
#     ) : (
#       <button onClick={handleConnectMicrosoft} className="...">
#         <OutlookIcon /> Connect Outlook
#       </button>
#     )
#   )}
# </div>
# 
# // Handler functions:
# const handleConnectGoogle = async () => {
#   const { authorization_url } = await api.request('/calendar/oauth/google/authorize');
#   window.location.href = authorization_url;
# };
# 
# const handleConnectMicrosoft = async () => {
#   const { authorization_url } = await api.request('/calendar/oauth/microsoft/authorize');
#   window.location.href = authorization_url;
# };
# 
# const handleDisconnectGoogle = async () => {
#   await api.request('/calendar/oauth/google/disconnect', { method: 'DELETE' });
#   setCalendarConnections(prev => ({
#     ...prev,
#     google: { ...prev.google, connected: false }
#   }));
# };
# 
# const handleDisconnectMicrosoft = async () => {
#   await api.request('/calendar/oauth/microsoft/disconnect', { method: 'DELETE' });
#   setCalendarConnections(prev => ({
#     ...prev,
#     microsoft: { ...prev.microsoft, connected: false }
#   }));
# };


# =============================================================================
# Environment Variables Template
# =============================================================================
# 
# Add these to your .env file when ready to enable external calendar integration:
# 
# # Google Calendar OAuth
# GOOGLE_CLIENT_ID=your_google_client_id_here
# GOOGLE_CLIENT_SECRET=your_google_client_secret_here
# GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/google/callback
# 
# # Microsoft Calendar OAuth
# MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
# MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
# MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/calendar/oauth/microsoft/callback
# MICROSOFT_AUTHORITY=https://login.microsoftonline.com/common
# 
# For production, update the redirect URIs to your actual domain:
# GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v1/calendar/oauth/google/callback
# MICROSOFT_REDIRECT_URI=https://yourdomain.com/api/v1/calendar/oauth/microsoft/callback

