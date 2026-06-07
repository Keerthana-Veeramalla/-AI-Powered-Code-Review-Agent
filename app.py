import streamlit as st
import requests
import json
import re
import os

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
)

def check_backend():
    try:
        r = requests.get(
            f"{BACKEND_URL}/",
            timeout=3
        )
        return r.status_code == 200
    except:
        return False

if not check_backend():
    st.warning(
        "Backend offline. Start uvicorn first: uvicorn main:app --reload"
    )

    
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""

""", unsafe_allow_html=True)


def fetch_gist_code(url: str):
    match = re.search(r'gist\.github\.com/[^/]+/([a-f0-9]+)', url)
    if not match:
        return "", "Invalid Gist URL format."
    gist_id = match.group(1)
    try:
        resp = requests.get(
            f"https://api.github.com/gists/{gist_id}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=10
        )
        if resp.status_code != 200:
            return "", f"GitHub returned error {resp.status_code}"
        files = resp.json().get("files", {})
        if not files:
            return "", "No files found in this Gist."
        first = list(files.values())[0]
        return first.get("content", ""), f"Loaded: {first.get('filename', 'file')}"

    except Exception as e:
        return "", f"Network error: {str(e)}"


def analyze_code(code: str, language: str):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/analyze",
            json={"code": code, "language": language},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Is uvicorn running?"
    except Exception as e:
        return None, str(e)


def stream_security_review(code: str, language: str):
    try:
        with requests.post(
            f"{BACKEND_URL}/analyze/stream",
            json={"code": code, "language": language},
            stream=True,
            timeout=60
        ) as resp:
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get("event") == "chunk":
                                yield data.get("text", "")
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        yield f"\n\nError: {str(e)}"


st.markdown("---")

st.markdown(
    "AI Code Review Agent · FastAPI + LangGraph + Groq LLaMA 3"
)

st.markdown(
    "Paste code or a GitHub Gist URL — get security analysis, unit tests, and explanation instantly.",
    unsafe_allow_html=True
)

col_input, col_options = st.columns([3, 1])

with col_options:
    st.markdown("#### Settings")
    
    language = st.selectbox(
        "Language",
        ["auto", "python", "javascript", "typescript", "java", "go"],
        help="auto = detect automatically from your code"
    )
    
    use_streaming = st.toggle(
        "Stream security review",
        value=True,
        help="Shows security review word by word as it's generated"
    )
    
    st.markdown("---")
    st.markdown("#### Load from GitHub Gist")
    
    gist_url = st.text_input(
        "Gist URL",
        placeholder="https://gist.github.com/user/abc123",
        label_visibility="collapsed"
    )
    
    if st.button("Fetch code", use_container_width=True):
        if gist_url.strip():
            with st.spinner("Fetching from GitHub..."):
                code_from_gist, msg = fetch_gist_code(gist_url.strip())
            if code_from_gist:
                st.session_state["gist_code"] = code_from_gist
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Enter a Gist URL first.")

with col_input:
    default_code = st.session_state.get("gist_code", "")
    
    code_input = st.text_area(
        "Paste your code here",
        value=default_code,
        height=320,
        placeholder="# Paste your code here, or fetch from a GitHub Gist URL on the right...\n\ndef example():\n    pass",
        label_visibility="collapsed"
    )

st.markdown("---")

analyse_btn = st.button(
    "Analyse code",
    type="primary",
    use_container_width=False,
    disabled=not bool(code_input.strip())
)

if analyse_btn:
    if not code_input.strip():
        st.warning("Please paste some code first.")
    else:
        tab_security, tab_tests, tab_explanation = st.tabs([
            "Security scan",
            "Unit tests",
            "Explanation"
        ])

        with tab_security:
            st.markdown("### Security analysis")
            if use_streaming:
                st.info("Streaming mode — security review appearing live below:")
                stream_output = st.empty()
                full_text = ""
                with st.spinner("Analysing security..."):
                    for chunk in stream_security_review(code_input, language):
                        full_text += chunk
                        stream_output.markdown(full_text)
                st.success("Security scan complete.")
            else:
                with st.spinner("Running all 3 agents in parallel..."):
                    result, error = analyze_code(code_input, language)
                if error:
                    st.error(error)
                else:
                    detected = result.get("detected_language", language)
                    st.caption(f"Detected language: {detected}")
                    st.markdown(result.get("security", "No result."))

        with tab_tests:
            st.markdown("### Generated unit tests")
            if use_streaming:
                with st.spinner("Generating tests (this runs in parallel)..."):
                    result, error = analyze_code(code_input, language)
                if error:
                    st.error(error)
                else:
                    detected = result.get("detected_language", language)
                    st.caption(f"Detected language: {detected}")
                    test_code = result.get("tests", "No result.")
                    st.code(test_code, language=result.get("language", "python"))
                    st.download_button(
                        "Download tests",
                        data=test_code,
                        file_name=f"test_generated.{result.get('language','py')}",
                        mime="text/plain"
                    )
            else:
                if result:
                    test_code = result.get("tests", "No result.")
                    st.code(test_code, language=result.get("language", "python"))
                    st.download_button(
                        "Download tests",
                        data=test_code,
                        file_name="test_generated.py",
                        mime="text/plain"
                    )

        with tab_explanation:
            st.markdown("### Code explanation")
            if result:
                st.markdown(result.get("explanation", "No result."))
            else:
                with st.spinner("Getting explanation..."):
                    result2, error2 = analyze_code(code_input, language)
                if error2:
                    st.error(error2)
                else:
                    st.markdown(result2.get("explanation", "No result."))

st.markdown("---")

st.markdown(
    "AI Code Review Agent · FastAPI + LangGraph + Groq LLaMA 3",
    unsafe_allow_html=True
)