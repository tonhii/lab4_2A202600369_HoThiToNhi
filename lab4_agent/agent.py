from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import sys
import io
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from tools import search_flights, search_hotels, calculate_budget

from dotenv import load_dotenv
load_dotenv()

# ================== LOAD PROMPT ==================

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ================== STATE ==================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ================== LLM + TOOLS ==================

tools_list = [search_flights, search_hotels, calculate_budget]

llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

# ================== AGENT NODE ==================

def agent_node(state: AgentState):
    messages = state["messages"]

    # thêm system prompt nếu chưa có
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # logging
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"🔧 Gọi tool: {tc['name']}({tc['args']})")
    else:
        print("💬 Trả lời trực tiếp")

    return {"messages": [response]}

# ================== BUILD GRAPH ==================

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# 🔥 QUAN TRỌNG NHẤT (thiếu là toang)

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    tools_condition,
)

builder.add_edge("tools", "agent")

# compile
graph = builder.compile()

# ================== CHAT LOOP ==================

if __name__ == "__main__":
    print("=" * 60)
    print("✈️ TravelBuddy — Trợ lý Du lịch")
    print("Gõ 'quit' để thoát")
    print("=" * 60)

    while True:
        user_input = input("\nBạn: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\n🤖 Đang suy nghĩ...\n")

        # ===== capture log nội bộ =====
        old_stdout = sys.stdout
        buffer = io.StringIO()
        sys.stdout = buffer

        try:
            result = graph.invoke({
                "messages": [("human", user_input)]
            })
        finally:
            sys.stdout = old_stdout

        log_output = buffer.getvalue()
        final = result["messages"][-1]

        # ===== in ra màn hình =====
        print(log_output)
        print(f"\nTravelBuddy: {final.content}")

        # ===== ghi vào file =====
        with open("test_results.md", "a", encoding="utf-8") as f:
            f.write("## Chat Session\n\n")
            f.write(f"**User:** {user_input}\n\n")
            f.write("```\n")
            f.write(log_output)
            f.write(f"\nFinal Answer:\n{final.content}\n")
            f.write("```\n\n---\n\n")