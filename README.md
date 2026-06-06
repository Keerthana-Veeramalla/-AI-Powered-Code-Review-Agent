# AI Code Review Agent

> Multi-agent AI that reviews code for security vulnerabilities,
> generates unit tests, and explains code — powered by LLaMA 3.3 70B.

**Live demo:** Coming soon

---

## Features

* Security scanner — finds SQL injection, hardcoded secrets, XSS, and more
* Unit test generator — writes pytest/Jest/JUnit tests automatically
* Code explainer — plain English walkthrough of any code
* Auto language detection — Python, JavaScript, TypeScript, Java, Go
* GitHub Gist integration — paste any Gist URL to fetch code instantly
* Streaming responses — security review streams token by token
* Parallel agents — all 3 agents run simultaneously, 3x faster

---

## Tech Stack

| Layer      | Technology                 |
| ---------- | -------------------------- |
| LLM        | LLaMA 3.3 70B via Groq API |
| Agents     | LangGraph + LangChain      |
| Backend    | FastAPI + Uvicorn          |
| Frontend   | Streamlit                  |
| Deployment | Render                     |

---

## Architecture

User Input (Code / Gist URL)

↓

Streamlit Frontend

↓

FastAPI Backend

↓

LangGraph Orchestrator

↓

Security Agent
Test Generator Agent
Code Explainer Agent

↓

Combined Response

↓

Streamlit Tabs

---

## Run Locally

Install dependencies:

pip install -r requirements.txt

Create a `.env` file:

GROQ_API_KEY=your_api_key_here

Start Backend:

uvicorn main:app --reload

Start Frontend:

streamlit run app.py

Open:

http://localhost:8501

---

## Project Structure

main.py → FastAPI backend

agents.py → Security, Test Generator, Explainer agents

graph.py → LangGraph orchestration

app.py → Streamlit frontend

requirements.txt → Dependencies

render.yaml → Render deployment configuration

---

Built by Keerthana
"# -AI-Powered-Code-Review-Agent" 
