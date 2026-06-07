from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2
)

llm_stream = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
    streaming=True
)

LANGUAGE_SECURITY_HINTS = {
    "python": "Also check: pickle deserialization, eval/exec usage, shell injection via subprocess, insecure random (use secrets module).",
    "javascript": "Also check: prototype pollution, eval usage, XSS via innerHTML, npm package vulnerabilities, JWT secret hardcoding.",
    "java": "Also check: deserialization vulnerabilities, XXE injection, JNDI injection (Log4Shell pattern), insecure reflection.",
    "typescript": "Same as JavaScript plus: type assertion abuse (as any), unsafe type casting.",
    "go": "Also check: SQL injection via fmt.Sprintf in queries, insecure TLS config, goroutine leaks.",
    "default": "Check for common vulnerabilities like injection, hardcoded secrets, and insecure data handling."
}

LANGUAGE_TEST_HINTS = {
    "python": "Use pytest. Import with: from your_module import function_name",
    "javascript": "Use Jest. Import with: const { functionName } = require('./yourModule')",
    "java": "Use JUnit 5. Annotate with @Test. Import org.junit.jupiter.api.*",
    "typescript": "Use Jest with ts-jest. Import with: import { functionName } from './yourModule'",
    "go": "Use Go testing package. Name test file *_test.go, functions TestXxx(t *testing.T)",
    "default": "Write clear unit tests covering normal, edge, and error cases."
}

def security_agent(code: str, language: str) -> str:
    lang_key = language.lower() if language.lower() in LANGUAGE_SECURITY_HINTS else "default"
    lang_hint = LANGUAGE_SECURITY_HINTS[lang_key]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a cybersecurity expert reviewing {language} code.
        
        Check ONLY for security issues:
        - SQL Injection risks
        - Hardcoded passwords, API keys, or secrets  
        - XSS vulnerabilities
        - Insecure data handling
        - Authentication/authorization flaws
        - Sensitive data exposure
        
        Language-specific checks: {lang_hint}
        
        Format response as:
        SEVERITY: [HIGH/MEDIUM/LOW/NONE]
        ISSUES FOUND: [list each issue]
        HOW TO FIX: [specific fix per issue]"""),
        ("human", "Review this {language} code for security issues:\n\n{code}")
    ])
    chain = prompt | llm
    result = chain.invoke({"language": language, "code": code})
    return result.content


def test_generator_agent(code: str, language: str) -> str:
    lang_key = language.lower() if language.lower() in LANGUAGE_TEST_HINTS else "default"
    lang_hint = LANGUAGE_TEST_HINTS[lang_key]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a senior engineer writing unit tests for {language} code.
        
        Rules:
        - {lang_hint}
        - Write tests for: happy path, edge cases, error cases
        - Add a comment on each test explaining what it checks
        - Return ONLY test code, no explanations"""),
        ("human", "Write unit tests for this {language} code:\n\n{code}")
    ])
    chain = prompt | llm
    result = chain.invoke({"language": language, "code": code})
    return result.content


def explainer_agent(code: str, language: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a senior {language} developer explaining code to a junior developer.
        
        Use these sections:
        WHAT IT DOES: One sentence summary
        HOW IT WORKS: Step by step walkthrough  
        KEY CONCEPTS: Important {language} patterns or concepts used
        USE CASE: When would you use this code
        
        Write in plain English. No jargon."""),
        ("human", "Explain this {language} code:\n\n{code}")
    ])
    chain = prompt | llm
    result = chain.invoke({"language": language, "code": code})
    return result.content


def security_agent_stream(code: str, language: str):
    lang_key = language.lower() if language.lower() in LANGUAGE_SECURITY_HINTS else "default"
    lang_hint = LANGUAGE_SECURITY_HINTS[lang_key]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a cybersecurity expert reviewing {language} code.
        Check for: SQL injection, hardcoded secrets, XSS, insecure handling.
        Language-specific: {lang_hint}
        Format: SEVERITY / ISSUES FOUND / HOW TO FIX"""),
        ("human", "Review this {language} code for security issues:\n\n{code}")
    ])
    chain = prompt | llm_stream
    for chunk in chain.stream({"language": language, "code": code}):
        yield chunk.content
