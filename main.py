from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph import run_agents_parallel
from agents import security_agent_stream
import json

app = FastAPI(title="Code Review Agent — Day 3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = [
    "python", "javascript", "typescript",
    "java", "go", "rust", "cpp", "csharp"
]

LANGUAGE_MARKERS = {
    "python": ["def ", "import ", "print(", "elif ", "__init__"],
    "javascript": ["const ", "let ", "var ", "=>", "console.log", "require("],
    "typescript": ["interface ", ": string", ": number", ": boolean", "as ", ""],
    "java": ["public class", "System.out", "void ", "String[] args", "@Override"],
    "go": ["func ", "package main", ":=", "fmt.Println", "goroutine"],
}

def detect_language(code: str) -> str:
    code_lower = code.lower()
    scores = {}
    for lang, markers in LANGUAGE_MARKERS.items():
        scores[lang] = sum(1 for m in markers if m.lower() in code_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "python"


class CodeRequest(BaseModel):
    code: str
    language: str = "auto"

class FullReviewResponse(BaseModel):
    security: str
    tests: str
    explanation: str
    language: str
    detected_language: str


@app.get("/")
def root():
    return {
        "message": "Code Review Agent v3 — streaming + multi-language!",
        "supported_languages": SUPPORTED_LANGUAGES
    }
@app.get("/languages")
def get_languages():
    return {"supported": SUPPORTED_LANGUAGES}


@app.post("/analyze", response_model=FullReviewResponse)
async def analyze_code(request: CodeRequest):
    detected = detect_language(request.code)
    language = detected if request.language == "auto" else request.language
    
    try:
        result = await run_agents_parallel(request.code, language)
        return FullReviewResponse(
            security=result["security"],
            tests=result["tests"],
            explanation=result["explanation"],
            language=language,
            detected_language=detected
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/stream")
async def stream_security_review(request: CodeRequest):
    detected = detect_language(request.code)
    language = detected if request.language == "auto" else request.language
    
    def generate():
        yield f"data: {json.dumps({'event': 'start', 'language': language})}\n\n"
        
        full_text = ""
        for chunk in security_agent_stream(request.code, language):
            if chunk:
                full_text += chunk
                yield f"data: {json.dumps({'event': 'chunk', 'text': chunk})}\n\n"
        
        yield f"data: {json.dumps({'event': 'done', 'full_text': full_text})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/detect-language")
def detect_lang_endpoint(code: str = Query(..., description="Code snippet to detect")):
    detected = detect_language(code)
    return {"detected_language": detected, "confidence": "based on syntax markers"}

