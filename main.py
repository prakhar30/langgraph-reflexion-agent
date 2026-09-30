from typing import Literal
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph, MessagesState

from chains import revision_chain, first_responder_chain
from tool_executor import execute_tools

MAX_ITERATIONS=2

def draft_node(state: MessagesState):
    """Draft the initial response"""
    response = first_responder_chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}

def revise_node(state: MessagesState):
    """Revise the answer based on the tool results"""
    response = revision_chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}

def event_loop(state: MessagesState) -> Literal["execute_tools", END]:
    """Determine whether to continue or end based on iteration count"""
    count_tool_visits = sum(isinstance(item, ToolMessage) for item in state["messages"])
    if count_tool_visits > MAX_ITERATIONS:
        return END
    return "execute_tools"

builder = StateGraph(MessagesState)
builder.add_node("draft", draft_node)
builder.add_node("execute_tools", execute_tools)
builder.add_node("revise", revise_node)

builder.add_edge(START, "draft")
builder.add_edge("draft", "execute_tools")
builder.add_edge("execute_tools", "revise")
builder.add_conditional_edges("revise", event_loop, ["execute_tools", END])

graph = builder.compile()
graph.get_graph().draw_mermaid_png(output_file_path="mermaid.png")

def main():
    print("Hello from reflexion-agent!")
    res = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Write about AI-Powered SOC / autonomous soc problem domain. List startups that do that and raised capital.",
                }
            ]
        }
    )
    print(res["messages"][-1])

if __name__ == "__main__":
    main()
