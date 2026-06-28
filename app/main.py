import os
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from duckduckgo_search import DDGS
import markdown

app = FastAPI()

# System prompt configured for clean layouts, tables, and live data
SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL RULES:\n"
    "1. Respond to simple greetings, casual text, or open-ended thoughts with regular, clean plain text. Do NOT use tables for simple chat.\n"
    "2. ONLY use a markdown table when the user explicitly asks for a table, a comparison, a differentiation, grammatical rules, or a structural matrix/formula layout.\n"
    "3. REAL-TIME DATA: If the user asks about current events, news, or weather, use the provided live search context details directly to answer. Summarize the major top headlines immediately. Do not ask the user to provide the context block.\n"
    "4. Keep descriptions brief, direct, and conversational so it fits clean, narrow e-ink viewports without long paragraphs or conversational fluff."
)

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.news(query, max_results=5)]
            if not results:
                return ""
            blob = "\n".join([f"Source: {r['title']}\nSnippet: {r['body']}" for r in results])
            return f"\n\n[Live Web Search Context]:\n{blob}"
    except Exception:
        return ""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    from app.templates import HTML_TEMPLATE
    page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", "")
    return HTMLResponse(content=page)

# FIXES THE ERROR: Explicitly defines the /clear endpoint to handle the template button cleanly
@app.get("/clear")
async def clear_chat():
    return RedirectResponse(url="/")

@app.post("/", response_class=HTMLResponse)
async def handle_inquiry(inquiry: str = Form(...)):
    from app.templates import HTML_TEMPLATE
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        error_html = "<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    search_keywords = ["search", "weather", "news", "today", "current", "latest", "globe"]
    context = ""
    if any(kw in inquiry.lower() for kw in search_keywords):
        context = search_web(inquiry)
        if not context:
            context = "\n\n[Live Web Search Context]: No live search connections available. Advise the user that Render's cloud servers are currently rate-limited by the search index."
        
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{inquiry}{context}"}
    ]
    
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
    return HTMLResponse(content=page)
