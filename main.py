import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

st.title("Life Coach Agent")

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        You are a warm, empathetic, and motivating life coach.
        Your goal is to help the user reflect on their life, set meaningful goals, and take actionable steps toward positive change.

        Guidelines:
        - Listen carefully and ask thoughtful follow-up questions.
        - Offer encouragement and practical advice.
        - Help the user break down big goals into small, manageable steps.
        - Use the Web Search Tool when the user asks about specific techniques, research, or current events related to self-improvement, habits, mental health, productivity, or any topic you're unsure about.
        - Always respond with compassion and positivity.
        """,
        tools=[
            WebSearchTool(),
        ],
    )
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "life-coach-session",
        "life-coach-memory.db",
    )
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔍 Searched the web...")


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                if event.data.type == "response.web_search_call.in_progress":
                    status_container.update(label="🔍 Searching the web...", state="running")
                elif event.data.type == "response.web_search_call.completed":
                    status_container.update(label="✅ Search completed.", state="complete")
                elif event.data.type == "response.completed":
                    status_container.update(label=" ", state="complete")
                elif event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)


prompt = st.chat_input("Tell me what's on your mind...")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    st.header("Memory")
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
        st.rerun()
