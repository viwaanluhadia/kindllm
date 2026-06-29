import os
import httpx
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
import markdown

app = FastAPI()

SESSION_STORAGE = {}

SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL INPUT INTERCEPT RULES:\n"
    "1. CASUAL CHAT: Respond to simple greetings or open thoughts with short plain text. No tables.\n"
    "2. DICTIONARY LOOKUP: If the input is a single word or asks 'define [word]', output a markdown table with headers: | Word | Part of Speech | Pronunciation | Core Definition | Etymology/Root |.\n"
    "3. CONCEPT COMPARISONS: If the input contains 'vs', 'difference', or 'compare', output a clean comparison markdown table evaluating key parameters side-by-side. Keep cell content ultra-short.\n"
    "4. TEXT SIMPLIFICATION: If the input starts with 'explain:' or 'eli5:', take the following text and break it down into ultra-crisp, short bullet points using completely simple language. Strip all academic jargon.\n"
    "5. GRAMMAR FORMULA MANDATE: When presenting tense structures, you MUST use standard explicit algebraic notation tokens: 'S', 'V1', 'V2', 'V3', 'V-ing', and 'Obj' (e.g., 'S + V1 + Obj').\n"
    "6. NO CONVERSATIONAL FLUFF: Never output introductory or concluding remarks (e.g., 'Here is your breakdown:'). Jump directly into the raw table, code, or summary text.\n"
    "7. CODE HANDLING: When displaying code syntax, wrap it inside standard markdown fences (e.g., ```python) so it renders in a clean monospaced font layout.\n"
    "8. REAL-TIME DATA: Use the attached '[Live India News Context]' data to summarize top headlines if asked about current events or news.\n"
    "9. Keep descriptions concise so it fits clean, narrow e-ink viewports without long paragraphs."
)

def fetch_live_news() -> str:
    url = "[https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en](https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en)"
    try:
        response = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            headlines = []
            for item in root.findall(".//item")[:7]:
                title = item.find("title").text if item.find("title") is not None else ""
                source = item.find("source").text if item.find("source") is not None else "National Feed"
                if title:
                    headlines.append(f"- Story: {title} (Source: {source})")
            if headlines:
                return "\n\n[Live India News Context]:\n" + "\n".join(headlines)
    except Exception:
        pass
    return ""

@app.get("/", response_class=HTMLResponse)
async def read_index(session_id: str = Cookie(None)):
    from app.templates import HTML_TEMPLATE
    response = HTMLResponse(content=HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", ""))
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
    
    if not session_id or session_id not in SESSION_STORAGE:
        session_id = str(uuid.uuid4())
        SESSION_STORAGE[session_id] = []
        
    history = SESSION_STORAGE[session_id]
    
    # Clean up the key string dynamically to strip off hidden newline tokens or carriage returns
    raw_key = os.getenv("LLM_API_KEY", "")
    api_key = raw_key.strip().replace('"', '').replace("'", "")
    
    if not api_key:
        error_html = "<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    search_keywords = ["search", "weather", "news", "today", "current", "latest", "globe", "world", "india"]
    context = ""
    if any(kw in inquiry.lower() for kw in search_keywords):
        context = fetch_live_news()
        
    history.append({"role": "user", "content": f"{inquiry}{context}"})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:]
    
    try:
        # Hardcoding the literal endpoint target string directly to completely rule out URL token parsing corruption
        endpoint_url = "[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                url=endpoint_url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.0}
            )
            res_json = res.json()
            
            if "choices" in res_json:
                raw_markdown = res_json["choices"][0]["message"]["content"]
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
