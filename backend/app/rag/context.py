"""RAG context builder — fetches base portfolio profile from DB."""

from __future__ import annotations

import json

from sqlalchemy import select

from app.database import async_session
from app.models.profile import Profile


async def get_base_portfolio_context() -> str:
    """Build a text context block from the user's profile data."""
    try:
        async with async_session() as db:
            result = await db.execute(select(Profile).limit(1))
            profile = result.scalar_one_or_none()

        if not profile:
            return "No profile found."

        context = "[Anurag's Core Profile Data]\n"
        context += f"Name: {profile.name}\n"
        if profile.header:
            context += f"Headline: {profile.header}\n"
        if profile.bio:
            context += f"Bio: {profile.bio}\n"
        if profile.skills:
            try:
                skills: dict[str, list[str]] = json.loads(profile.skills)
                context += "Skills:\n"
                for category, items in skills.items():
                    context += f"- {category}: {', '.join(items)}\n"
            except (json.JSONDecodeError, TypeError):
                context += f"Skills: {profile.skills}\n"

        availability = (
            f"Open to Work (Available {profile.availableFrom or 'immediately'}, "
            f"Notice Period: {profile.noticePeriod or 'N/A'})"
            if profile.openToWork
            else "Currently employed / Not looking"
        )
        context += f"Current Status: {availability}\n"
        context += "[End Profile Data]\n"

        return context

    except Exception as e:
        print(f"[context.builder] Error fetching base profile: {e}")
        return ""
