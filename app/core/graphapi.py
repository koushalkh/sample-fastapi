"""
Microsoft Graph API client for email operations.

This module provides reusable functions to interact with Microsoft Graph API
for email-related operations like sending emails, reading messages, etc.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import httpx
from structlog import get_logger

from .config import settings

logger = get_logger()


class GraphAPIError(Exception):
    """Custom exception for Graph API errors."""
    pass


class GraphAPIClient:
    """Microsoft Graph API client for email operations."""
    
    def __init__(self):
        self.base_url = settings.graph_api_endpoint
        self.tenant_id = settings.tenant_id
        self.client_id = settings.client_id
        self.client_secret = settings.client_secret
        self.scopes = settings.graph_api_scopes
        self._access_token = None
        self._token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """Get access token using client credentials flow."""
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise GraphAPIError("Missing required Graph API credentials. Check environment variables.")
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data: Dict[str, str] = {
            "client_id": str(self.client_id),
            "client_secret": str(self.client_secret),
            "scope": " ".join(self.scopes),
            "grant_type": "client_credentials"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 minute buffer
                
                logger.info("Successfully obtained Graph API access token")
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error("Failed to obtain access token", status_code=e.response.status_code, response=e.response.text)
                raise GraphAPIError(f"Failed to obtain access token: {e.response.status_code}")
            except Exception as e:
                logger.error("Error obtaining access token", error=str(e))
                raise GraphAPIError(f"Error obtaining access token: {str(e)}")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to Graph API."""
        token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise GraphAPIError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                if response.status_code == 204:  # No content
                    return {}
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error("Graph API request failed", 
                           method=method, 
                           endpoint=endpoint, 
                           status_code=e.response.status_code, 
                           response=e.response.text)
                raise GraphAPIError(f"Graph API request failed: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error("Error making Graph API request", method=method, endpoint=endpoint, error=str(e))
                raise GraphAPIError(f"Error making Graph API request: {str(e)}")
    
    async def send_email(self, 
                        to_recipients: List[str],
                        subject: str,
                        body: str,
                        body_type: str = "HTML",
                        cc_recipients: Optional[List[str]] = None,
                        bcc_recipients: Optional[List[str]] = None,
                        sender_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email using Graph API.
        
        Args:
            to_recipients: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: Body content type ("HTML" or "Text")
            cc_recipients: List of CC recipient email addresses
            bcc_recipients: List of BCC recipient email addresses
            sender_email: Sender email address (if not provided, uses application's default)
        
        Returns:
            Response from Graph API
        """
        def format_recipients(emails: List[str]) -> List[Dict[str, Any]]:
            return [{"emailAddress": {"address": email}} for email in emails]
        
        message_data: Dict[str, Any] = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body
                },
                "toRecipients": format_recipients(to_recipients)
            }
        }
        
        if cc_recipients:
            message_data["message"]["ccRecipients"] = format_recipients(cc_recipients)
        
        if bcc_recipients:
            message_data["message"]["bccRecipients"] = format_recipients(bcc_recipients)
        
        # Determine endpoint based on whether sender is specified
        if sender_email:
            endpoint = f"users/{sender_email}/sendMail"
        else:
            endpoint = "me/sendMail"
        
        logger.info("Sending email", 
                   to_count=len(to_recipients), 
                   cc_count=len(cc_recipients) if cc_recipients else 0,
                   bcc_count=len(bcc_recipients) if bcc_recipients else 0,
                   subject=subject)
        
        return await self._make_request("POST", endpoint, message_data)
    
    async def get_messages(self, 
                          user_email: Optional[str] = None,
                          folder: str = "inbox",
                          top: int = 10,
                          filter_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get messages from a user's mailbox.
        
        Args:
            user_email: User email address (if not provided, uses application's default)
            folder: Folder name (inbox, sent, drafts, etc.)
            top: Number of messages to retrieve
            filter_query: OData filter query
        
        Returns:
            Response containing messages
        """
        if user_email:
            endpoint = f"users/{user_email}/mailFolders/{folder}/messages"
        else:
            endpoint = f"me/mailFolders/{folder}/messages"
        
        params = [f"$top={top}"]
        
        if filter_query:
            params.append(f"$filter={filter_query}")
        
        if params:
            endpoint += "?" + "&".join(params)
        
        logger.info("Retrieving messages", user_email=user_email, folder=folder, top=top)
        
        return await self._make_request("GET", endpoint)
    
    async def get_message_by_id(self, 
                               message_id: str,
                               user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Message ID
            user_email: User email address (if not provided, uses application's default)
        
        Returns:
            Message details
        """
        if user_email:
            endpoint = f"users/{user_email}/messages/{message_id}"
        else:
            endpoint = f"me/messages/{message_id}"
        
        logger.info("Retrieving message", message_id=message_id, user_email=user_email)
        
        return await self._make_request("GET", endpoint)
    
    async def mark_message_as_read(self, 
                                  message_id: str,
                                  user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Mark a message as read.
        
        Args:
            message_id: Message ID
            user_email: User email address (if not provided, uses application's default)
        
        Returns:
            Response from Graph API
        """
        if user_email:
            endpoint = f"users/{user_email}/messages/{message_id}"
        else:
            endpoint = f"me/messages/{message_id}"
        
        data: Dict[str, bool] = {"isRead": True}
        
        logger.info("Marking message as read", message_id=message_id, user_email=user_email)
        
        return await self._make_request("PATCH", endpoint, data)
    
    async def delete_message(self, 
                            message_id: str,
                            user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a message.
        
        Args:
            message_id: Message ID
            user_email: User email address (if not provided, uses application's default)
        
        Returns:
            Response from Graph API
        """
        if user_email:
            endpoint = f"users/{user_email}/messages/{message_id}"
        else:
            endpoint = f"me/messages/{message_id}"
        
        logger.info("Deleting message", message_id=message_id, user_email=user_email)
        
        return await self._make_request("DELETE", endpoint)
    
    async def get_user_profile(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            user_email: User email address (if not provided, uses application's default)
        
        Returns:
            User profile information
        """
        if user_email:
            endpoint = f"users/{user_email}"
        else:
            endpoint = "me"
        
        logger.info("Retrieving user profile", user_email=user_email)
        
        return await self._make_request("GET", endpoint)


# Global instance for convenience
graph_client = GraphAPIClient()


# Convenience functions
async def send_email(to_recipients: List[str],
                    subject: str,
                    body: str,
                    **kwargs: Any) -> Dict[str, Any]:
    """Convenience function to send an email."""
    return await graph_client.send_email(to_recipients, subject, body, **kwargs)


async def get_inbox_messages(user_email: Optional[str] = None, 
                           top: int = 10) -> Dict[str, Any]:
    """Convenience function to get inbox messages."""
    return await graph_client.get_messages(user_email=user_email, top=top)


async def get_user_profile(user_email: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get user profile."""
    return await graph_client.get_user_profile(user_email)
