import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="StudyMate", page_icon="📚", layout="centered")
st.title("📚 StudyMate")
st.caption("주제 학습 · 플래시카드 · 퀴즈 · 보충 학습을 도와드리는 멀티 에이전트 학습 도우미")


from graph import graph

# 세션 상태 초기화
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "msg_count" not in st.session_state:
    st.session_state.msg_count = 0

# 사이드바
with st.sidebar:
    st.header("🤖 에이전트 정보")

    agent_labels = {
        "classification_agent": "🏠 분류 에이전트",
        "tutor_agent": "📖 튜터 에이전트",
        "quiz_agent": "📝 퀴즈 에이전트",
        "researcher_agent": "🔍 리서처 에이전트",
    }

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    try:
        state = graph.get_state(config)
        current = state.values.get("current_agent", "classification_agent")
        st.write(f"현재 담당: **{agent_labels.get(current, current)}**")
    except Exception:
        st.write("현재 담당: **🏠 분류 에이전트**")

    st.divider()

    st.markdown(
        "**사용법**\n"
        "1. 공부할 주제를 입력하세요\n"
        "2. 플래시카드로 개념을 익히세요\n"
        "3. 퀴즈로 이해도를 확인하세요\n"
        "4. 틀린 개념은 보충 학습!"
    )

    st.divider()

    if st.button("🔄 대화 초기화"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.msg_count = 0
        st.rerun()

# 대화 기록 표시
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input("무엇을 공부하고 싶으세요?")

if user_input:
    # 사용자 메시지 표시
    with st.chat_message("human"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "human", "content": user_input})

    # 그래프 실행
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.spinner("생각 중..."):
        # 실행 전 메시지 수 기록
        before_count = st.session_state.msg_count

        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # 새로 생성된 AI 메시지만 추출 (이전에 표시한 것 제외)
        all_messages = result["messages"]
        new_ai_messages = [
            m for m in all_messages[before_count:]
            if isinstance(m, AIMessage) and m.content and m.content.strip()
        ]

        # 현재까지의 전체 메시지 수 저장
        st.session_state.msg_count = len(all_messages)

    # 새 AI 메시지들을 각각 표시
    for msg in new_ai_messages:
        with st.chat_message("ai"):
            st.markdown(msg.content)
        st.session_state.chat_history.append(
            {"role": "ai", "content": msg.content}
        )

    st.rerun()
