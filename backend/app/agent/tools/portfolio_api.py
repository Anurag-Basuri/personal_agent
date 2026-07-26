"""Portfolio API tool   fetches live data from the portfolio website's public REST API.

Instead of duplicating the portfolio database schema, this tool makes HTTP GET requests
to the portfolio's existing public endpoints. This ensures the agent always gets the
exact same data as the frontend, with zero sync issues.

Supported categories:
  - profile: Bio, skills, location, availability, social links, coding platforms
  - projects: All published portfolio projects with tech stacks
  - journey: Work experience, education, research, volunteering
  - achievements: Hackathons, awards, competitions, scholarships
  - certifications: Professional certifications with credentials
  - blog: Published articles and posts
"""

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.core.cache import TTLCache
from app.core.retry import retry_with_backoff

# Cache API responses to avoid hammering the portfolio server
# 5 minutes
_api_cache = TTLCache(default_ttl=300)

# API Endpoint Mapping
_CATEGORY_ENDPOINTS = {
    "profile": "/profile",
    "projects": "/projects",
    "journey": "/journey",
    "achievements": "/achievements",
    "certifications": "/certifications",
    "blog": "/blog",
}


# HTTP Fetch Layer
async def _fetch_portfolio_endpoint(url: str) -> httpx.Response:
    """Make a GET request to a portfolio API endpoint."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "PersonalAgent/2.0",
                "Accept": "application/json",
            },
        )
        return response


# Response Formatters
def _format_profile(data: dict) -> str:
    """Format the profile API response into readable text."""
    lines = [f"# {data.get('name', 'Anurag Basuri')}'s Profile\n"]

    if data.get("Tagline"):
        lines.append(f"**Tagline**: {data['Tagline']}")
    if data.get("header"):
        lines.append(f"**Headline**: {data['header']}")
    if data.get("bio"):
        lines.append(f"\n**Bio**: {data['bio']}")
    if data.get("pronouns"):
        lines.append(f"**Pronouns**: {data['pronouns']}")

    # Location
    loc_parts = []
    if data.get("Currentlocation"):
        loc_parts.append(f"Currently in {data['Currentlocation']}")
    if data.get("Originallocation"):
        loc_parts.append(f"Originally from {data['Originallocation']}")
    if loc_parts:
        lines.append(f"**Location**: {' | '.join(loc_parts)}")

    # Job Availability
    lines.append(f"\n**Open to Work**: {'✅ Yes' if data.get('openToWork') else '❌ No'}")
    if data.get("availableFrom"):
        lines.append(f"**Available From**: {data['availableFrom']}")
    if data.get("noticePeriod"):
        lines.append(f"**Notice Period**: {data['noticePeriod']}")
    if data.get("Freelancing"):
        lines.append("**Freelancing**: ✅ Available for freelance work")

    # Work Preferences
    prefs = data.get("workPreferences")
    if prefs and isinstance(prefs, dict):
        pref_list = [k for k, v in prefs.items() if v]
        if pref_list:
            lines.append(f"**Work Preferences**: {', '.join(pref_list)}")

    # Skills
    skills = data.get("skills")
    if skills:
        if isinstance(skills, dict):
            lines.append("\n**Skills**:")
            for category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    lines.append(f"  - {category}: {', '.join(skill_list)}")
                else:
                    lines.append(f"  - {category}: {skill_list}")
        elif isinstance(skills, str):
            lines.append(f"\n**Skills**: {skills}")

    # Quick Stats
    if data.get("experienceYears"):
        lines.append(f"**Years of Experience**: {data['experienceYears']}")
    if data.get("projectsCount"):
        lines.append(f"**Projects Count**: {data['projectsCount']}")

    # Languages
    languages = data.get("languages")
    if languages and isinstance(languages, list):
        lines.append(f"**Languages Spoken**: {', '.join(languages)}")

    # Resume
    if data.get("resumeUrl"):
        lines.append(f"\n**Resume**: [Download Resume]({data['resumeUrl']})")

    # Social Links
    social_links = data.get("socialLinks", [])
    if social_links:
        lines.append("\n**Social Links**:")
        for link in social_links:
            platform = link.get("platform", link.get("customLabel", "Link"))
            url = link.get("url", "")
            lines.append(f"  - {platform}: {url}")

    # Coding Platform URLs
    coding_platforms = []
    for platform in ["github", "leetcode", "codeforces", "codechef", "gfg", "kaggle", "hackerrank", "stackoverflow"]:
        url = data.get(platform)
        if url:
            coding_platforms.append(f"  - {platform.capitalize()}: {url}")
    if coding_platforms:
        lines.append("\n**Coding Profiles**:")
        lines.extend(coding_platforms)

    return "\n".join(lines)


def _format_projects(data: list) -> str:
    """Format the projects API response into readable text."""
    if not data:
        return "No published projects found in the portfolio."

    lines = [f"Found {len(data)} published projects:\n"]
    for p in data:
        lines.append(f"### {p.get('title', 'Untitled')}")
        if p.get("description"):
            desc = p["description"]
            if len(desc) > 300:
                desc = desc[:300] + "..."
            lines.append(f"**Description**: {desc}")

        tech = p.get("techStack")
        if tech:
            if isinstance(tech, list):
                lines.append(f"**Tech Stack**: {', '.join(tech)}")
            else:
                lines.append(f"**Tech Stack**: {tech}")

        if p.get("stars") is not None:
            lines.append(f"⭐ Stars: {p['stars']} | 🍴 Forks: {p.get('forks', 0)}")
        if p.get("liveUrl"):
            lines.append(f"**Live Demo**: {p['liveUrl']}")
        if p.get("githubUrl"):
            lines.append(f"**GitHub**: {p['githubUrl']}")
        lines.append("")

    return "\n".join(lines)


def _format_journey(data: list) -> str:
    """Format the journey API response into readable text."""
    if not data:
        return "No journey entries found."

    lines = [f"Found {len(data)} career/education entries:\n"]
    for j in data:
        entry_type = j.get("type", "OTHER")
        title = j.get("title", "Untitled")
        org = j.get("organization", "")
        date = j.get("date", "")
        is_current = j.get("isCurrent", False)

        header = f"### [{entry_type}] {title}"
        if org:
            header += f" at {org}"
        lines.append(header)

        if date:
            lines.append(f"**Period**: {date}" + (" (Current)" if is_current else ""))
        if j.get("location"):
            lines.append(f"**Location**: {j['location']}")
        if j.get("description"):
            desc = j["description"]
            if len(desc) > 500:
                desc = desc[:500] + "..."
            lines.append(f"**Description**: {desc}")

        # Education specific
        if j.get("degree"):
            lines.append(f"**Degree**: {j['degree']}" + (f" in {j['fieldOfStudy']}" if j.get("fieldOfStudy") else ""))
        if j.get("grade"):
            lines.append(f"**Grade**: {j['grade']}")

        # Work specific
        if j.get("employmentType"):
            lines.append(f"**Employment Type**: {j['employmentType']}")
        if j.get("workMode"):
            lines.append(f"**Work Mode**: {j['workMode']}")

        # Skills
        skills = j.get("skills", [])
        if skills and isinstance(skills, list):
            lines.append(f"**Skills**: {', '.join(skills)}")

        # Achievements linked to this journey entry
        achievements = j.get("achievements", [])
        if achievements:
            lines.append(f"**Achievements ({len(achievements)}):**")
            for a in achievements[:5]:
                lines.append(f"  - {a.get('title', '')} ({a.get('rank', '')})")

        lines.append("")

    return "\n".join(lines)


def _format_achievements(data: list) -> str:
    """Format achievements API response."""
    if not data:
        return "No achievements found."

    lines = [f"Found {len(data)} achievements:\n"]
    for a in data:
        lines.append(f"### 🏆 {a.get('title', 'Untitled')}")
        if a.get("category"):
            lines.append(f"**Category**: {a['category']}")
        if a.get("issuer"):
            lines.append(f"**Issuer**: {a['issuer']}")
        if a.get("event"):
            lines.append(f"**Event**: {a['event']}")
        if a.get("rank"):
            lines.append(f"**Rank**: {a['rank']}")
        if a.get("description"):
            desc = a["description"]
            if len(desc) > 300:
                desc = desc[:300] + "..."
            lines.append(f"**Description**: {desc}")
        tags = a.get("tags", [])
        if tags and isinstance(tags, list):
            lines.append(f"**Tags**: {', '.join(tags)}")
        team = a.get("team", [])
        if team and isinstance(team, list):
            lines.append(f"**Team**: {', '.join(team)}")
        if a.get("proofUrl"):
            lines.append(f"**Proof**: {a['proofUrl']}")
        lines.append("")

    return "\n".join(lines)


def _format_certifications(data: list) -> str:
    """Format certifications API response."""
    if not data:
        return "No certifications found."

    lines = [f"Found {len(data)} certifications:\n"]
    for c in data:
        lines.append(f"### 📜 {c.get('title', 'Untitled')}")
        if c.get("issuer"):
            lines.append(f"**Issuer**: {c['issuer']}")
        if c.get("description"):
            desc = c["description"]
            if len(desc) > 300:
                desc = desc[:300] + "..."
            lines.append(f"**Description**: {desc}")
        if c.get("credentialId"):
            lines.append(f"**Credential ID**: {c['credentialId']}")
        if c.get("credentialUrl"):
            lines.append(f"**Verify**: {c['credentialUrl']}")
        skills = c.get("skills", [])
        if skills and isinstance(skills, list):
            lines.append(f"**Skills**: {', '.join(skills)}")
        lines.append("")

    return "\n".join(lines)


def _format_blog(data: list) -> str:
    """Format blog posts API response."""
    if not data:
        return "No published blog posts found."

    lines = [f"Found {len(data)} published blog posts:\n"]
    for b in data:
        lines.append(f"### 📝 {b.get('title', 'Untitled')}")
        tags = b.get("tags", [])
        if tags and isinstance(tags, list):
            lines.append(f"**Tags**: {', '.join(tags)}")
        if b.get("publishedAt"):
            lines.append(f"**Published**: {b['publishedAt'][:10]}")
        if b.get("content"):
            # Provide a summary (first 500 chars)
            content = b["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"**Preview**: {content}")
        if b.get("link"):
            lines.append(f"**Read More**: {b['link']}")
        lines.append("")

    return "\n".join(lines)


_FORMATTERS = {
    "profile": _format_profile,
    "projects": _format_projects,
    "journey": _format_journey,
    "achievements": _format_achievements,
    "certifications": _format_certifications,
    "blog": _format_blog,
}


# The Tool
@tool
async def portfolio_api_tool(category: str) -> str:
    """Fetch live data from Anurag's portfolio website.

    Use this tool to answer ANY question about Anurag's background, skills, work, or portfolio content.

    Categories (pick ONE):
    - "profile": Bio, skills, location, availability, work preferences, social links, coding platform URLs, resume
    - "projects": All published portfolio projects with tech stacks, live demos, GitHub repos
    - "journey": Work experience, education, research, volunteering history with details
    - "achievements": Hackathons won, awards, competitions, scholarships, publications
    - "certifications": Professional certifications with credential links and skills
    - "blog": Published articles and blog posts

    IMPORTANT CHAINING RULES:
    - If the user asks about a SPECIFIC project's architecture or "how did you build X", 
      first call this tool with category="projects" to find the githubUrl,
      then use the read_github_readme tool with the owner and repo extracted from that URL.
    - If the user asks a question that might span multiple categories (e.g., "tell me everything about you"),
      call this tool multiple times with different categories.
    """
    settings = get_settings()
    portfolio_url = settings.PORTFOLIO_URL

    if not portfolio_url:
        return "Portfolio URL is not configured. Cannot fetch portfolio data."

    # Normalize category
    cat = category.strip().lower()
    if cat not in _CATEGORY_ENDPOINTS:
        return (
            f'Unknown category "{category}". '
            f'Available categories: {", ".join(_CATEGORY_ENDPOINTS.keys())}'
        )

    # Check cache
    cache_key = f"portfolio_api:{cat}"
    cached = _api_cache.get(cache_key)
    if cached:
        return cached

    # Build the full API URL
    endpoint = _CATEGORY_ENDPOINTS[cat]
    url = f"{portfolio_url.rstrip('/')}/api/v1{endpoint}"

    try:
        response = await retry_with_backoff(
            _fetch_portfolio_endpoint,
            url,
            max_retries=2,
            base_delay=1.0,
            retryable_exceptions=(httpx.TimeoutException, httpx.RequestError),
            operation_name=f"Portfolio_API_{cat}",
        )

        if response.status_code != 200:
            return (
                f"Portfolio API returned status {response.status_code} for {cat}. "
                f"The portfolio server might be down or the endpoint has changed."
            )

        json_data = response.json()

        # Portfolio API wraps responses in { success: true, data: ... }
        actual_data = json_data.get("data", json_data)

        # Format the response
        formatter = _FORMATTERS.get(cat)
        if formatter:
            result = formatter(actual_data)
        else:
            result = str(actual_data)

        _api_cache.set(cache_key, result)
        return result

    except Exception as e:
        return f"Error fetching portfolio {cat} data: {e}"
