import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered
from models import CustomerContext
from my_agents.triage_agent import triage_agent


customer_ctx = CustomerContext(
    customer_id=1,
    name="Soo",
    tier="regular",
    phone="010-1234-5678",
)


st.set_page_config(page_title="Seoul Bistro — Restaurant Bot", page_icon="🍽️")
st.title("🍽️ Seoul Bistro")
st.caption(
    f"메뉴 · 주문 · 예약을 도와드리는 레스토랑 봇입니다. (고객: {customer_ctx.name}, 등급: {customer_ctx.tier})"
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-session",
        "restaurant-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", r"\$"))


asyncio.run(paint_history())


async def run_agent(message):

    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""

        try:

            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=customer_ctx,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", r"\$"))

                elif event.type == "agent_updated_stream_event":

                    if st.session_state["agent"].name != event.new_agent.name:

                        st.write(
                            f"🔄 {st.session_state['agent'].name} → {event.new_agent.name} 로 연결합니다..."
                        )

                        st.session_state["agent"] = event.new_agent

                        text_placeholder = st.empty()
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.write("죄송합니다, 저는 메뉴 · 주문 · 예약만 도와드릴 수 있어요.")


message = st.chat_input("무엇을 도와드릴까요? (예: 7시에 4명 예약하고 싶어요)")

if message:
    with st.chat_message("human"):
        st.write(message)
    asyncio.run(run_agent(message))


with st.sidebar:
    st.header(f"👤 {customer_ctx.name}")
    st.write(f"현재 담당: **{st.session_state['agent'].name}**")
    reset = st.button("대화 초기화")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["agent"] = triage_agent
        st.rerun()
    st.divider()
    st.caption("로그")
