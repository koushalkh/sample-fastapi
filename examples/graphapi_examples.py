"""
Example usage of the GraphAPI module.

This file demonstrates how to use the Graph API functions for email operations.
"""

from app.core.graphapi import GraphAPIClient, send_email, get_inbox_messages


async def example_send_email():
    """Example of sending an email using the Graph API."""
    try:
        # Send a simple email
        result = await send_email(
            to_recipients=["user@example.com"],
            subject="Test Email from FastAPI App",
            body="<h1>Hello!</h1><p>This is a test email sent via Microsoft Graph API.</p>",
            body_type="HTML"
        )
        print("Email sent successfully!")
        return result
    except Exception as e:
        print(f"Failed to send email: {e}")


async def example_send_email_with_cc():
    """Example of sending an email with CC recipients."""
    try:
        # Create a client instance
        client = GraphAPIClient()
        
        result = await client.send_email(
            to_recipients=["primary@example.com"],
            cc_recipients=["cc1@example.com", "cc2@example.com"],
            subject="Project Update",
            body="Please find the project update attached.",
            body_type="Text"
        )
        print("Email with CC sent successfully!")
        return result
    except Exception as e:
        print(f"Failed to send email with CC: {e}")


async def example_get_messages():
    """Example of retrieving inbox messages."""
    try:
        # Get the latest 5 messages from inbox
        messages = await get_inbox_messages(top=5)
        
        print(f"Retrieved {len(messages.get('value', []))} messages")
        
        for message in messages.get('value', []):
            print(f"Subject: {message.get('subject')}")
            print(f"From: {message.get('from', {}).get('emailAddress', {}).get('address')}")
            print(f"Received: {message.get('receivedDateTime')}")
            print("---")
            
        return messages
    except Exception as e:
        print(f"Failed to get messages: {e}")


async def example_get_user_profile():
    """Example of getting user profile information."""
    try:
        # Create a client instance
        client = GraphAPIClient()
        
        profile = await client.get_user_profile()
        
        print(f"User: {profile.get('displayName')}")
        print(f"Email: {profile.get('mail') or profile.get('userPrincipalName')}")
        print(f"Job Title: {profile.get('jobTitle')}")
        
        return profile
    except Exception as e:
        print(f"Failed to get user profile: {e}")


async def example_mark_message_as_read():
    """Example of marking a message as read."""
    try:
        # First get some messages
        messages = await get_inbox_messages(top=1)
        
        if messages.get('value'):
            message_id = messages['value'][0]['id']
            
            # Create a client instance
            client = GraphAPIClient()
            
            # Mark the first message as read
            await client.mark_message_as_read(message_id)
            print(f"Message {message_id} marked as read")
        else:
            print("No messages found to mark as read")
    except Exception as e:
        print(f"Failed to mark message as read: {e}")


# Environment variables needed:
# TENANT_ID=your-tenant-id
# CLIENT_ID=your-client-id  
# CLIENT_SECRET=your-client-secret
# GRAPH_API_SCOPES=https://graph.microsoft.com/.default (optional)

if __name__ == "__main__":
    print("Graph API Examples")
    print("Make sure to set the required environment variables:")
    print("- TENANT_ID")
    print("- CLIENT_ID") 
    print("- CLIENT_SECRET")
    print()
    
    # Run examples (uncomment the ones you want to test)
    # asyncio.run(example_send_email())
    # asyncio.run(example_send_email_with_cc())
    # asyncio.run(example_get_messages())
    # asyncio.run(example_get_user_profile())
    # asyncio.run(example_mark_message_as_read())
