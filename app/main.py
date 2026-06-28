import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from jinja2 import Template
import httpx
from duckduckgo_search import DDGS
from app.templates import HTML_TEMPLATE

app = FastAPI()
template_engine = Template(HTML_TEMPLATE)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = os.environ.get("LLM_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def home():
    initial_text = "KindLLM Online with Live Web Search. Ask me anything current."
    rendered_html = template_engine.render(prompt="", response=initial_text)
    return HTMLResponse(content=rendered_html)

@app.post("/", response_class=HTMLResponse)
async def handle_prompt(prompt: str = Form(...)):
    if not API_KEY:
        rendered_html = template_engine.render(
            prompt=prompt, 
            response="Error: Server missing LLM_API_KEY."
        )
        return HTMLResponse(content=rendered_html)

    # 1. Fetch real-time web context before querying the LLM
    web_context = ""
    try:
        with DDGS() as ddgs:
            search_results = [r for r in ddgs.text(prompt, max_results=3)]
            web_context = "\n".join([f"Source: {res['body']}" for res in search_results])
    except Exception:
        web_context = "No recent web data pulled due to connection limits."

    # 2. Package context inside the payload
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": (
                    "You are KindLLM, a hyper-accurate reading assistant for an e-ink Kindle device. "
                    "You are given real-time web snippets to accurately answer recent events or dynamic facts. "
                    "Respond in clean, brief paragraphs. Strictly avoid markdown asterisks (**), bullet blocks, or code tags, "
                    "as they break formatting on basic e-ink setups. Keep the spacing elegant."
                )
            },
            {
                "role": "user", 
                "content": f"Live Web Context:\n{web_context}\n\nUser Question: {prompt}"
            }
        ],
        "temperature": 0.3
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
            else:
                ai_response = f"API Error: Received code {response.status_code} from provider."
        except httpx.RequestError as exc:
            ai_response = f"Network Connection Failure: {exc}"

    rendered_html = template_engine.render(prompt=prompt, response=ai_response)
    return HTMLResponse(content=rendered_html)
