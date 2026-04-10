"""Contact form submission tool — saves visitor inquiries to the DB."""

import json
import uuid

import bleach
from langchain_core.tools import tool

from app.database import async_session
from app.models.contact import ContactMessage


@tool
async def contact_tool(name: str, email: str, message: str) -> str:
    """Submit an inquiry, job offer, or contact message to Anurag.
    You MUST ask the user for their name, email, and message explicitly before calling this tool."""
    try:
        # Sanitize inputs
        clean_name = bleach.clean(name, tags=[], strip=True)
        clean_email = bleach.clean(email, tags=[], strip=True)
        clean_message = bleach.clean(message, tags=[], strip=True)

        async with async_session() as db:
            contact = ContactMessage(
                id=str(uuid.uuid4()).replace("-", "")[:25],
                name=clean_name,
                email=clean_email,
                subject="Contact Form via AI Agent",
                message=clean_message,
                isRead=False,
            )
            db.add(contact)
            await db.commit()

        return json.dumps({
            "success": True,
            "notification": "Successfully saved the message to the database. Anurag will see this in his admin dashboard.",
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Database error occurred while saving the lead: {e}",
        })
