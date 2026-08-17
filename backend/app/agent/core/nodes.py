"""LangGraph nodes: Intent Router, LLM invocation (via orchestrator), and Tool Execution.

Resilience patterns applied:
  - Centralized LLMOrchestrator handles the 6-layer cascade internally
    (circuit breakers, smart error classification, per-tier timeouts)
  - Tool execution uses retry_with_backoff for transient failures
  - Layer 6 static fallback (never crashes)
  - Graceful degradation tracking via SystemHealth

The call_model and call_tools functions use get_all_tools by default.
For the public portfolio chatbot, use make_call_model(tools_getter)
and make_call_tools(tools_getter) to inject a restricted toolset.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from app.agent.core.state import AgentState
from app.agent.llm import thinker, reasoner
from app.agent.tools import get_all_tools
from app.core.logger import agent_logger
from app.core.retry import retry_with_backoff


# Layer 6: Static Fallback Message
# This is the safety net. If all 5 LLM tiers fail (rate limits,
# network errors, circuit breakers all OPEN), this message is
# returned to the user. It NEVER fails because it's pure Python.
STATIC_FALLBACK_MESSAGE = (
    "I'm temporarily unable to process your request as all my AI providers "
    "are experiencing issues. Please try again in a few minutes. "
    "I apologize for the inconvenience!"
)


# Keywords for fast intent classification
_GREETING_PATTERNS = {
    "hi", "hello", "hey", "howdy", "sup", "yo", "what's up",
    "good morning", "good evening", "good afternoon", "greetings",
    "namaste", "hola",
}

_META_PATTERNS = {
    "who are you", "what can you do", "help", "what are you",
    "how do you work", "what tools", "capabilities",
}

_CONVERSATIONAL_PATTERNS = {
    "thanks", "thank you", "thx", "ty", "cool", "nice", "awesome",
    "okay", "ok", "got it", "understood", "sure", "alright",
    "what now", "what next", "what else", "anything else",
    "good", "great", "perfect", "fine", "sounds good",
    "bye", "goodbye", "see you", "later", "goodnight", "good night",
    "lol", "haha", "hehe", "lmao", "wow", "hmm", "oh", "ah",
    "yes", "no", "yeah", "yep", "nope", "nah",
    "how are you", "how's it going", "what's happening",
}

# Compact persona for Thinker (greeting/meta/conversational intents only)
def get_slim_persona(role: str) -> str:
    if role == "ADMIN":
        return (
            "You are Cortex, a sharp and proactive AI assistant built by Anurag Basuri. "
            "You serve only Anurag. ALWAYS address him as 'Boss' or 'Sir'. "
            "Be conversational, warm, concise, and highly efficient. Keep responses under 2 sentences."
        )
    return (
        "You are Anurag Basuri's AI assistant, embedded on his portfolio. "
        "ALWAYS speak as Anurag in the first person (e.g., 'I built', 'My experience'). "
        "Be conversational, warm, and concise. Keep responses under 2 sentences."
    )


async def route_intent(state: AgentState) -> dict:
    """
    Lightweight intent classifier -- routes messages to skip tools when unnecessary.

    Intents:
      - "greeting": Simple hello/hi -> skip tools, direct LLM reply
      - "meta_question": Questions about the agent itself -> skip tools
      - "tool_use": Everything else -> full agent+tools cycle
    """
    messages = state["messages"]

    # Find the last human message
    user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_msg = str(msg.content).strip().lower()
            break

    if not user_msg:
        return {"intent": "tool_use"}

    intent = classify_intent(user_msg)
    agent_logger.debug("ROUTER", f"Intent: {intent} -- '{user_msg[:40]}'")
    ret = {"intent": intent}

    # Dynamic Tool Routing for Admin (to prevent 233-tool overload)
    if intent == "tool_use" and state.get("role") == "ADMIN":
        try:
            from pydantic import BaseModel, Field
            from app.mcp.client import mcp_manager
            
            available_servers = [k for k, v in mcp_manager.get_status().items() if v == "connected"]
            
            if available_servers:
                # Build server descriptions for the routing prompt
                _SERVER_HINTS = {
                    "google": "Gmail, Calendar, Contacts, Drive (Google Workspace)",
                    "github": "GitHub repos, issues, PRs, code search",
                    "linear": "Linear project management, issues, cycles",
                    "todoist": "Todoist tasks, projects, labels",
                    "notion": "Notion pages, databases, blocks",
                    "vercel": "Vercel deployments, domains, projects",
                    "netlify": "Netlify sites, deploys, DNS",
                    "render": "Render services, deploys, databases",
                    "zomato": "Zomato restaurant search and food ordering",
                    "swiggy_food": "Swiggy food delivery and restaurant search",
                    "swiggy_instamart": "Swiggy Instamart grocery delivery",
                    "swiggy_dineout": "Swiggy Dineout restaurant reservations",
                    "quickcommerce": "Quick commerce delivery (Blinkit, Zepto)",
                    "hacker_news": "Hacker News stories, comments, search",
                    "duckduckgo": "Web search via DuckDuckGo",
                    "sequential_thinking": "Step by step reasoning and analysis",
                    "puppeteer": "Browser automation, screenshots, web scraping",
                    "postgres": "Direct PostgreSQL database queries",
                }
                server_list = "\n".join(
                    f"  - {s}: {_SERVER_HINTS.get(s, 'Unknown')}"
                    for s in available_servers
                )

                class MCPRouting(BaseModel):
                    needed_servers: list[str] = Field(
                        description=f"List of MCP servers needed. Options: {', '.join(available_servers)}"
                    )
                
                providers = thinker.get_providers()
                if providers:
                    prompt = (
                        "You are a precise routing agent. Select ONLY the MCP servers strictly necessary "
                        "for the user's request. Do NOT add servers that are not directly needed.\n\n"
                        f"User Request: {user_msg}\n\n"
                        f"Available Servers:\n{server_list}"
                    )
                    
                    # Try each provider in the cascade for robust structured output routing
                    for provider in providers:
                        if provider.disabled:
                            continue
                        try:
                            structured_llm = provider.llm.with_structured_output(MCPRouting)
                            res = await structured_llm.ainvoke(prompt)
                            
                            # Ensure only valid servers are returned
                            valid_servers = [s for s in res.needed_servers if s in available_servers]
                            ret["active_servers"] = valid_servers
                            agent_logger.debug("ROUTER", f"Activated servers: {valid_servers} (via {provider.provider_name})")
                            break # Success!
                        except Exception as e:
                            agent_logger.warn("ROUTER", f"Provider {provider.provider_name} failed routing: {e}")
                            continue # Try next provider
                            
                    # If all providers failed, we must not return None (which enables all 233 tools)
                    if "active_servers" not in ret:
                        agent_logger.warn("ROUTER", "All providers failed routing. Falling back to zero MCP tools to prevent crashes.")
                        ret["active_servers"] = []
        except Exception as e:
            agent_logger.warn("ROUTER", f"Failed to dynamically route servers: {e}")
            ret["active_servers"] = []  # fallback to loading zero MCP tools, NEVER None
            
    return ret


def classify_intent(user_msg: str) -> str:
    """Fast keyword-based intent classification for a single string."""
    cleaned = user_msg.lower().rstrip("!?.,:;")

    if cleaned in _GREETING_PATTERNS or any(cleaned.startswith(g) for g in _GREETING_PATTERNS):
        return "greeting"

    if any(p in user_msg for p in _META_PATTERNS):
        return "meta_question"

    # Short conversational follow-ups (under 8 words, no question structure)
    word_count = len(cleaned.split())
    if word_count <= 8:
        if cleaned in _CONVERSATIONAL_PATTERNS or any(cleaned.startswith(p) for p in _CONVERSATIONAL_PATTERNS):
            return "conversational"

    return "tool_use"


def _build_slim_messages(messages: list, role: str) -> list:
    """
    Build a compact message list for the Thinker brain.

    Strips RAG context, tool schemas, memories, and portfolio data.
    Keeps only a minimal system prompt and the last few conversation turns.
    Target: ~500-800 tokens (well within Groq's 6,000 TPM limit).
    """
    from langchain_core.messages import SystemMessage as SM

    slim_system = SM(content=get_slim_persona(role))

    # Collect only the last few human/AI messages (skip System/Tool messages)
    recent = []
    for msg in reversed(messages):
        if msg.type in ("human", "ai") and not getattr(msg, "tool_calls", []):
            content = str(msg.content).strip()
            if content:
                recent.append(msg)
        if len(recent) >= 4:
            break
    recent.reverse()

    return [slim_system, *recent]


def sanitize_message_history(messages: list) -> list:
    """
    Strip tool call metadata from message history for LLM safety.

    Gemini strictly requires AIMessage(tool_calls) to be immediately
    followed by matching ToolMessages. Old history from trimming,
    interrupted sessions, or cross-session replay can violate this.

    The simplest bulletproof fix: strip all tool_call metadata from
    history. The LLM only needs the conversation text, not old
    tool call IDs from previous turns.
    """
    sanitized = []
    for msg in messages:
        # Remove ToolMessages entirely (old tool responses)
        if msg.type == "tool":
            continue

        # Strip tool_calls from AIMessages, keep only the text content
        if msg.type == "ai" and getattr(msg, "tool_calls", []):
            content = str(msg.content).strip() if msg.content else ""
            if content:
                sanitized.append(AIMessage(content=content))
            continue

        sanitized.append(msg)

    return sanitized


def make_call_model(tools_getter=get_all_tools):
    """Factory: returns a call_model node wired to the given tools getter."""

    async def _call_model(state: AgentState):
        """
        Invoke the LLM using the centralized orchestrator.

        The orchestrator handles the entire 6-layer cascade internally:
          - Smart error classification (permanent/rate_limited/transient)
          - Per-tier circuit breakers
          - Hard per-attempt timeouts (10s)
          - Runtime tier disabling for 404s

        If all tiers fail, returns Layer 6 static message (never crashes).
        """
        messages = state["messages"]
        role = state.get("role", "GUEST")
        # Determine which tools to activate
        intent = state.get("intent", "tool_use")
        active_servers = state.get("active_servers")

        # Bind all currently available tools via the getter
        try:
            available_tools = tools_getter(active_servers)
        except TypeError:
            available_tools = tools_getter()

        allowed_tools = []
        for t in available_tools:
            if getattr(t, "requires_admin", False) and role != "ADMIN":
                continue
            allowed_tools.append(t)

        # Delegate to the appropriate brain
        if intent in ("greeting", "meta_question", "conversational"):
            # Brain 1: Fast, slim context, no tools needed
            slim_messages = _build_slim_messages(messages, role)
            response = await thinker.invoke(slim_messages, None)
        else:
            # Brain 2: Deep reasoning with tools (sanitized history)
            safe_messages = sanitize_message_history(messages)
            response = await reasoner.invoke(safe_messages, allowed_tools or None)

        if response is not None:
            # Anti-infinite-loop protection for weaker models (e.g. Mistral)
            if getattr(response, "tool_calls", []):
                for msg in reversed(safe_messages):
                    if getattr(msg, "tool_calls", []):
                        if msg.tool_calls == response.tool_calls:
                            agent_logger.warn("LLM", f"Detected infinite tool-calling loop on {msg.tool_calls[0].get('name', 'unknown')}, breaking out.")
                            response.tool_calls = []
                            if not response.content:
                                response.content = "I have fetched the information."
                        break

            return {"messages": [response]}

        # Thinker dynamic fallback
        # If the Reasoner completely failed, don't crash to the static string immediately.
        # Ask the Thinker to gracefully apologize to the user and offer alternatives.
        agent_logger.warn("LLM", "Reasoner cascade exhausted. Falling back to Thinker for graceful apology.")
        
        fallback_prompt = SystemMessage(
            content="System Alert: The primary reasoning engine just failed due to API rate limits or network errors. "
                    "You (the fast Thinker model) must now apologize to the user on behalf of the system. "
                    "Explain briefly that complex tasks are temporarily unavailable, and ask them if they'd like "
                    "to explore something else or ask a simpler question. Be polite and conversational. DO NOT attempt to use tools."
        )
        
        fallback_messages = _build_slim_messages(messages, role)
        fallback_messages.append(fallback_prompt)
        
        fallback_response = await thinker.invoke(fallback_messages, None)
        
        if fallback_response is not None:
            return {"messages": [fallback_response]}

        # Layer 6: Static Fallback
        # Only reached if the Thinker also completely crashes!
        agent_logger.error(
            "LLM",
            "[STATIC] ALL LLM tiers (including Thinker fallback) exhausted -- returning static fallback",
            None,
            {"tiers_configured": len(thinker.get_providers()) + len(reasoner.get_providers())},
        )
        return {"messages": [AIMessage(content=STATIC_FALLBACK_MESSAGE)]}

    return _call_model


# Default call_model uses get_all_tools (backward compatible)
call_model = make_call_model(get_all_tools)


def make_call_tools(tools_getter: Callable[[], list] = get_all_tools):
    """Factory: returns a call_tools node wired to the given tools getter."""

    async def _call_tools(state: AgentState):
        """Executes the requested tools with retry for transient failures."""
        # The last message is the AIMessage with tool_calls
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        if not tool_calls:
            return {"messages": []}

        tool_map = {t.name: t for t in tools_getter()}
        results = []

        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_args = tc.get("args", {})
            tool_id = tc.get("id")

            selected = tool_map.get(tool_name)
            if not selected:
                agent_logger.warn("TOOL", f'Tool "{tool_name}" not found', {"args": tool_args})
                msg = ToolMessage(
                    tool_call_id=tool_id,
                    content=f"Tool {tool_name} not found or unauthorized.",
                    name=tool_name,
                )
                results.append(msg)
                continue

            t_start = agent_logger.tool_start(tool_name, tool_args)
            try:
                # Retry tool execution for transient failures
                tool_output = await retry_with_backoff(
                    selected.ainvoke,
                    tool_args,
                    max_retries=2,
                    base_delay=0.5,
                    max_delay=5.0,
                    retryable_exceptions=(TimeoutError, ConnectionError),
                    operation_name=f"Tool:{tool_name}",
                )
                output_str = str(tool_output)
                agent_logger.tool_success(tool_name, t_start, output_str)

                msg = ToolMessage(
                    tool_call_id=tool_id,
                    content=output_str,
                    name=tool_name,
                )
                results.append(msg)
            except Exception as e:
                agent_logger.tool_error(tool_name, t_start, e)
                msg = ToolMessage(
                    tool_call_id=tool_id,
                    content=f"Failed to execute tool: {e}",
                    name=tool_name,
                )
                results.append(msg)

        return {"messages": results}

    return _call_tools


# Default call_tools uses get_all_tools (backward compatible)
call_tools = make_call_tools(get_all_tools)
