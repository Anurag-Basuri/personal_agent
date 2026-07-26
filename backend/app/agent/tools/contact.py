"""Contact form tool — submits visitor inquiries via the portfolio's public API.

Instead of writing directly to the database, this tool makes a POST request
to the portfolio's /api/v1/contact endpoint, which handles sanitization,
rate limiting, and IP logging on its own.
"""

import json

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.core.retry import retry_with_backoff


async def _submit_contact(url: str, payload: dict) -> httpx.Response:
    """POST the contact form data to the portfolio API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PersonalAgent/2.0",
            },
        )


@tool
async def contact_tool(name: str, email: str, subject: str, message: str) -> str:
    """Submit an inquiry, job offer, or contact message to Anurag via his portfolio's contact form.
    You MUST ask the user for their name, email, and message explicitly before calling this tool.
    The subject should be auto-generated based on context (e.g., 'Job Inquiry via AI Agent')."""
    settings = get_settings()
    portfolio_url = settings.PORTFOLIO_URL

    if not portfolio_url:
        return json.dumps({
            "success": False,
            "error": "Portfolio URL is not configured. Cannot submit contact form.",
        })

    url = f"{portfolio_url.rstrip('/')}/api/v1/contact"

    try:
        response = await retry_with_backoff(
            _submit_contact,
            url,
            {"name": name, "email": email, "subject": subject, "message": message},
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(httpx.TimeoutException, httpx.RequestError),
            operation_name="Portfolio_Contact_Submit",
        )

        if response.status_code in (200, 201):
            return json.dumps({
                "success": True,
                "notification": "Message sent successfully! Anurag will see this in his dashboard.",
            })

        # Handle rate limiting from the portfolio API
        if response.status_code == 429:
            return json.dumps({
                "success": False,
                "error": "Too many contact submissions. Please try again later.",
            })

        return json.dumps({
            "success": False,
            "error": f"Portfolio API returned status {response.status_code}. Please try again.",
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to submit contact form: {e}",
        })
