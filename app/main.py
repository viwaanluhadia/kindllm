import os
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from duckduckgo_search import DDGS
import markdown

app = FastAPI()

# System prompt optimized for structural layout (Tables, Lists, Bold text)
SYSTEM_PROMPT = (
    "You are a strict, minimalist data assistant for an e-ink Kindle screen. "
    "CRITICAL RULE: Never write comparisons, rules, lists, or structured data as long paragraphs. "
    "If the user asks for rules, comparisons, or differentiation, you MUST use a clean markdown table. "
    "Use '| Column |' syntax to build standard tables. Keep text inside cells brief and high-contrast."
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
    # Render empty state
    return HTML_TEMPLATE.format(inquiry="", response="")

@app.post("/", response_class=HTMLResponse)
async def handle_inquiry(inquiry: str = Form(...)):
    from app.templates import HTML_TEMPLATE
    
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return HTML_TEMPLATE.format(inquiry=inquiry, response="<p style='color:red;'>Error: LLM_API_KEY environment variable is missing.</p>")
    
    # Check if the query asks for fresh information to trigger search
    search_keywords = ["search", "weather", "news", "today", "current", "latest", "versus", "diff", "compare"]
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
                json={"model": "llama3-70b-8192",, "messages": messages, "temperature": 0.3}
            )
            res_json = res.json()
            raw_markdown = res_json["choices"][0]["message"]["content"]
            
            # Convert the markdown response (including tables) into HTML
            html_response = markdown.markdown(raw_markdown, extensions=['tables', 'fenced_code'])
            
    except Exception as e:
        html_response = f"<p style='color:red;'>Connection Error: {str(e)}</p>"
        
    return HTML_TEMPLATE.format(inquiry=inquiry, response=html_response)
