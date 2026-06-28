import os
import httpx
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
import markdown

app = FastAPI()

# Simple in-memory storage for chat histories keyed by session ID
SESSION_STORAGE = {}

SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL RULES:\n"
    "1. Respond to simple greetings, casual text, or open-ended thoughts with regular, clean plain text. Do NOT use tables for simple chat.\n"
    "2. ONLY use a markdown table when the user explicitly asks for a table, a comparison, a differentiation, grammatical rules, or a structural matrix/formula layout.\n"
    "3. REAL-TIME DATA: If the user asks about current events, news, or global updates, use the attached '[Live Google News Context]' data to summarize the top breaking news stories right now. Keep it brief, factual, and direct.\n"
    "4. CONTEXT MEMORY: You have access to the conversation history. Maintain the flow of the discussion naturally when the user asks follow-up questions.\n"
    "5. Keep descriptions concise so it fits clean, narrow e-ink viewports without long paragraphs or conversational fluff."
)

def fetch_live_news() -> str:
    """Fetches top global headlines via Google News RSS."""
    url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    try:
        response = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            headlines = []
            for item in root.findall(".//item")[:7]:
                title = item.find("title").text if item.find("title") is not None else ""
                source = item.find("source").text if item.find("source") is not None else "Global Feed"
                if title:
                    headlines.append(f"- Story: {title} (Source: {source})")
            if headlines:
                return "\n\n[Live Google News Context]:\n" + "\n".join(headlines)
    except Exception:
        pass
    return ""

@app.get("/", response_class=HTMLResponse)
async def read_index(session_id: str = Cookie(None)):
    from app.templates import HTML_TEMPLATE
    response = HTMLResponse(content=HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", ""))
    
    # Assign a unique session ID if the user doesn't have one
    if not session_id:
        new_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=new_id, httponly=True)
        SESSION_STORAGE[new_id] = []
    return response

@app.get("/clear")
async def clear_chat(session_id: str = Cookie(None)):
    if session_id in SESSION_STORAGE:
        SESSION_STORAGE[session_id] = []
    return RedirectResponse(url="/")

@app.post("/", response_class=HTMLResponse)
async def handle_inquiry(inquiry: str = Form(...), session_id: str = Cookie(None)):
    from app.templates import HTML_TEMPLATE
    
    # Ensure session tracking exists
    if not session_id or session_id not in SESSION_STORAGE:
        session_id = str(uuid.uuid4())
        SESSION_STORAGE[session_id] = []
        
    history = SESSION_STORAGE[session_id]
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        error_html = "<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    search_keywords = ["search", "weather", "news", "today", "current", "latest", "globe", "world", "earthquake"]
    context = ""
    if any(kw in inquiry.lower() for kw in search_keywords):
        context = fetch_live_news()
        
    # Append user input to ongoing memory thread
    history.append({"role": "user", "content": f"{inquiry}{context}"})
    
    # Keep historical logs capped to the last 6 iterations to protect token limits
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.2}
            )
            res_json = res.json()
            
            if "choices" in res_json:
                raw_markdown = res_json["choices"][0]["message"]["content"]
                # Save assistant response to memory thread
                history.append({"role": "assistant", "content": raw_markdown})
                html_response = markdown.markdown(raw_markdown, extensions=['tables', 'fenced_code'])
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
    if session_id:
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response
