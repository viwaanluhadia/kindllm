import os
import httpx
import json
import urllib.parse
from fastapi import FastAPI, Request, Form, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from duckduckgo_search import DDGS
import markdown

app = FastAPI()

SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL RULES:\n"
    "1. Respond to simple greetings, casual text, or open-ended thoughts with regular, clean plain text. Do NOT use tables for simple chat.\n"
    "2. ONLY use a markdown table when the user explicitly asks for a table, a comparison, a differentiation, grammatical rules, or a structural matrix/formula layout.\n"
    "3. REAL-TIME DATA: If the user asks about current events, news, or weather, use the provided live search context details directly to answer. Summarize major points immediately. Never state you lack access if data is appended below.\n"
    "4. CONVERSATION HISTORY: You are part of a continuous conversation. Use the chat history to understand follow-up questions, pronouns, or context. Keep descriptions brief, direct, and conversational."
)

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=4)]
            if not results:
                return ""
            blob = "\n".join([f"Source: {r['title']}\nContext: {r['body']}" for r in results])
            return f"\n\n[Live Web Search Context]:\n{blob}"
    except Exception:
        return ""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    from app.templates import HTML_TEMPLATE
    page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", "")
    return HTMLResponse(content=page)

@app.get("/clear")
@app.post("/clear")
async def clear_chat():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="chat_history")
    return response

@app.post("/", response_class=HTMLResponse)
async def handle_inquiry(
    inquiry: str = Form(...),
    chat_history: str = Cookie(default=None)
):
    from app.templates import HTML_TEMPLATE
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        error_html = "<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    history = []
    if chat_history:
        try:
            history = json.loads(urllib.parse.unquote(chat_history))
        except Exception:
            history = []

    # Detect if search is triggered
    search_keywords = ["search", "weather", "news", "today", "current", "latest"]
    is_search_query = any(kw in inquiry.lower() for kw in search_keywords)
    
    context = ""
    if is_search_query:
        context = search_web(inquiry)
        if not context:
            context = "\n\n[Live Web Search Context]: No active search results found. Summarize general ongoing global occurrences."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Safely inject past history turns
    for turn in history[-6:]:
        # CRITICAL FIX: If we are looking up real-time news right now, strip out old hallucinated data restrictions from memory
        if is_search_query and "real-time data" in turn["assistant"].lower():
            continue
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
        
    messages.append({"role": "user", "content": f"{inquiry}{context}"})
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.3}
            )
            res_json = res.json()
            
            if "choices" in res_json:
                raw_markdown = res_json["choices"][0]["message"]["content"]
                html_response = markdown.markdown(raw_markdown, extensions=['tables', 'fenced_code'])
                history.append({"user": inquiry, "assistant": raw_markdown})
            else:
                error_msg = res_json.get("error", {}).get("message", "Unknown API Response")
                html_response = f"<p style='color:red;'>API Error: {error_msg}</p>"
                
    except Exception as e:
        html_response = f"<p style='color:red;'>Connection Error: {str(e)}</p>"
        
    dynamic_content = f"""
    <div class="section-label">Inquiry</div>
    <div class="query-text">{inquiry}</div>
    <div class="section-label">Response</div>
    <div class="response-body">{html_response}</div>
    """
    
    page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", dynamic_content)
    response = HTMLResponse(content=page)
    
    updated_history_str = urllib.parse.quote(json.dumps(history[-8:]))
    response.set_cookie(key="chat_history", value=updated_history_str, max_age=86400, httponly=True)
    
    return response
