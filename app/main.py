import os
import httpx
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
import markdown

app = FastAPI()

SESSION_STORAGE = {}

# Rebalanced Rule 1 to skip rigid heading hierarchies for simple greetings and conversational texts
SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL RESPONDING RULES:\n"
    "1. SCANNABLE FORMAT MANDATE: For informative, technical, or analytical queries, you MUST break the response down using bold markdown headings (### Heading) to segment distinct ideas. Under each heading, write naturally in clean, concise prose paragraphs. Use bullet points ONLY for explicit lists.\n"
    "2. CHAT & GREETING EXCEPTION: For short greetings, casual chat, or single-sentence text (e.g., 'hi', 'hello', 'ok', 'thank you'), do NOT create structured headings or markdown titles. Just respond with a brief, friendly, single-line plain text statement.\n"
    "3. ONLY use a markdown table when the user explicitly asks for a table, a comparison, a differentiation, grammatical rules, or a structural matrix/formula layout.\n"
    "4. GRAMMAR FORMULA MANDATE: When presenting tense structures, you MUST use standard explicit algebraic notation tokens: 'S', 'V1', 'V2', 'V3', 'V-ing', and 'Obj' (e.g., 'S + V1 + Obj').\n"
    "5. REAL-TIME DATA: If the user asks about current events, news, or regional updates, use the attached '[Live India News Context]' data to summarize the top breaking news stories immediately. Keep it brief, factual, and direct.\n"
    "6. NO CONVERSATIONAL FLUFF: Never output introductory or concluding sentences like 'Here is the breakdown:' or 'I hope this helps' before tables or analytical data. Jump directly into the raw layout.\n"
    "7. CONTEXT MEMORY: You have access to the conversation history. Maintain the flow of the discussion naturally when the user asks follow-up questions.\n"
    "8. Keep descriptions concise so it fits clean, narrow e-ink viewports without long paragraphs."
)

def search_web(query: str) -> str:
    url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
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
    page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", "")
    response = HTMLResponse(content=page)
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
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        error_html = "<div style='color:red;'>Error: LLM_API_KEY is missing.</div>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    search_keywords = ["search", "weather", "news", "today", "current", "latest", "globe", "world", "india", "earthquake"]
    context = ""
    if any(kw in inquiry.lower() for kw in search_keywords):
        context = search_web(inquiry)
        
    history.append({"role": "user", "content": f"{inquiry}{context}"})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-6:]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
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
                html_response = f"<div style='color:red;'>API Error: {error_msg}</div>"
                
    except Exception as e:
        html_response = f"<div style='color:red;'>Connection Error: {str(e)}</div>"
        
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
