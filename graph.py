from langgraph.graph import StateGraph, END
from typing import TypedDict
from agents import security_agent, test_generator_agent, explainer_agent
import asyncio

class AgentState(TypedDict):
    code: str
    language: str
    security_result: str
    tests_result: str
    explanation_result: str

def run_security(state: AgentState) -> AgentState:
    result = security_agent(state["code"], state["language"])
    return {"security_result": result}

def run_tests(state: AgentState) -> AgentState:
    result = test_generator_agent(state["code"], state["language"])
    return {"tests_result": result}

def run_explainer(state: AgentState) -> AgentState:
    result = explainer_agent(state["code"], state["language"])
    return {"explanation_result": result}

def build_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("security", run_security)
    graph.add_node("tests", run_tests)
    graph.add_node("explainer", run_explainer)
    
    graph.set_entry_point("security")
    graph.add_edge("security", "tests")
    graph.add_edge("tests", "explainer")
    graph.add_edge("explainer", END)
    
    return graph.compile()

agent_graph = build_graph()


async def run_agents_parallel(code: str, language: str) -> dict:
    loop = asyncio.get_event_loop()
    
    security_task = loop.run_in_executor(
        None, security_agent, code, language
    )
    tests_task = loop.run_in_executor(
        None, test_generator_agent, code, language
    )
    explainer_task = loop.run_in_executor(
        None, explainer_agent, code, language
    )
    
    security_result, tests_result, explanation_result = await asyncio.gather(
        security_task, tests_task, explainer_task
    )
    
    return {
        "security": security_result,
        "tests": tests_result,
        "explanation": explanation_result
    }
