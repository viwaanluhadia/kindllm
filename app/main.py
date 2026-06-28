import os
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from duckduckgo_search import DDGS
import markdown

app = FastAPI()

# Updated prompt to explicitly force the model to read real-time context data
SYSTEM_PROMPT = (
    "You are a minimalist, highly efficient reading companion optimized for a Kindle screen.\n\n"
    "CRITICAL RULES:\n"
    "1. Respond to simple greetings, casual text, or open-ended thoughts with regular, clean plain text. Do NOT use tables for simple chat.\n"
    "2. ONLY use a markdown table when the user explicitly asks for a table, a comparison, a differentiation, grammatical rules, or a structural matrix/formula layout.\n"
    "3. REAL-TIME DATA: If the user asks about current events, news, or weather, you will see a '[Live Web Search Context]' attached to their message. You MUST use this data to provide the latest real-time updates. Never claim you don't have access to real-time information if the context block is provided.\n"
    "4. Keep descriptions brief, direct, and conversational so it fits clean, narrow e-ink viewports without long paragraphs or conversational fluff."
)

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
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

@app.post("/", response_class=HTMLResponse)
async def handle_inquiry(inquiry: str = Form(...)):
    from app.templates import HTML_TEMPLATE
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        error_html = "<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>"
        page = HTML_TEMPLATE.replace("RENDERED_CONTENT_PLACEHOLDER", error_html)
        return HTMLResponse(content=page)
    
    search_keywords = ["search", "weather", "news", "today", "current", "latest"]
    context = ""
    if any(kw in inquiry.lower() for kw in search_keywords):
        context = search_web(inquiry)
        
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
