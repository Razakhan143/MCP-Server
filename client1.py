import os
import json
import asyncio
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage


SERVERS = { 
    "math": {
        "transport": "stdio",
        "command": "C:\\Users\\tesla\\anaconda3\\Scripts\\uv.exe",
        "args": [
            "run",
            "fastmcp",
            "run",
            "C:\\Users\\tesla\\Desktop\\MCP-Server\\calculator.py"
       ]
    },
    "Time-tracking": {
        "transport": "streamable_http",  # if this fails, try "sse"
        "url": "https://vocal-black-wolverine.fastmcp.app/mcp"
    },
    "jobspy": {
      "transport": "stdio",
      "command": "node",
      "args": ["C:\\Users\\tesla\\Desktop\\MCP-Server\\jobspy-mcp-server\\src\\index.js"],
      "env": {
        "ENABLE_SSE": "0"
      }
    }

}
SYSTEM_PROMPT = (
    "You have access to tools. When you choose to call a tool, do not narrate status updates. "
    "After tools run, return only a concise final answer."
)

st.set_page_config(page_title="MCP Chat", page_icon="🧰", layout="centered")
st.title("🧰 MCP Chat")
# One-time init
if "initialized" not in st.session_state:
    # 1) LLM
    from langchain_openai import ChatOpenAI
    st.session_state.llm =ChatOpenAI (
model="xiaomi/mimo-v2-flash:free",
# api_key=os.getenv ("OPENAI API KEY"),
api_key=os.getenv ("OR_API_KEY"),
base_url="https://openrouter.ai/api/v1",
max_tokens=4000

)

    # 2) MCP tools
    st.session_state.client = MultiServerMCPClient(SERVERS)
    tools = asyncio.run(st.session_state.client.get_tools())
    st.session_state.tools = tools
    st.session_state.tool_by_name = {t.name: t for t in tools}

    # 3) Bind tools
    st.session_state.llm_with_tools = st.session_state.llm.bind_tools(tools)

    # 4) Conversation state
    st.session_state.history = [SystemMessage(content=SYSTEM_PROMPT)]
    st.session_state.initialized = True

# Render chat history (skip system + tool messages; hide intermediate AI with tool_calls)
for msg in st.session_state.history:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        # Skip assistant messages that contain tool_calls (intermediate “fetching…”)
        if getattr(msg, "tool_calls", None):
            continue
        with st.chat_message("assistant"):
            st.markdown(msg.content)
    # ToolMessage and SystemMessage are not rendered as bubbles

# Chat input
user_text = st.chat_input("Type a message…")
if user_text:
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.history.append(HumanMessage(content=user_text))

    # First pass: let the model decide whether to call tools
    first = asyncio.run(st.session_state.llm_with_tools.ainvoke(st.session_state.history))
    tool_calls = getattr(first, "tool_calls", None)
    print("Tool calls:", tool_calls)
# print tool results in JSON format
    print("Full first response:", first.json())
    if not tool_calls:
        # No tools → show & store assistant reply
        with st.chat_message("assistant"):
            st.markdown(first.content or "")
        st.session_state.history.append(first)
    else:
        # ── IMPORTANT ORDER ──
        # 1) Append assistant message WITH tool_calls (do NOT render)
        st.session_state.history.append(first)

        # 2) Execute requested tools and append ToolMessages (do NOT render)
        tool_msgs = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            tool = st.session_state.tool_by_name[name]
            res = asyncio.run(tool.ainvoke(args))
            tool_msgs.append(ToolMessage(tool_call_id=tc["id"], content=json.dumps(res)))

        st.session_state.history.extend(tool_msgs)

        # 3) Final assistant reply using tool outputs → render & store
        final = asyncio.run(st.session_state.llm.ainvoke(st.session_state.history))
        with st.chat_message("assistant"):
            st.markdown(final.content or "")
        st.session_state.history.append(AIMessage(content=final.content or ""))