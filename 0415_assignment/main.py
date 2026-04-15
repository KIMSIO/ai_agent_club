import dotenv

dotenv.load_dotenv()

import asyncio
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI
from agents import Agent, FileSearchTool, Runner, SQLiteSession, WebSearchTool


APP_DIR = Path(__file__).parent
VECTOR_STORE_META = APP_DIR / ".vector_store.json"
UPLOAD_DIR = APP_DIR / "uploaded_docs"
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_STORE_NAME = "life-coach-goals"

client = OpenAI()


def load_vector_store_meta():
    if VECTOR_STORE_META.exists():
        return json.loads(VECTOR_STORE_META.read_text(encoding="utf-8"))
    return {}


def save_vector_store_meta(meta):
    VECTOR_STORE_META.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def ensure_vector_store():
    meta = load_vector_store_meta()
    vs_id = meta.get("vector_store_id")
    if vs_id:
        try:
            client.vector_stores.retrieve(vs_id)
            return vs_id
        except Exception:
            pass

    vs = client.vector_stores.create(name=VECTOR_STORE_NAME)
    save_vector_store_meta({"vector_store_id": vs.id, "files": []})
    return vs.id


def upload_file_to_vector_store(vs_id, file_path):
    with open(file_path, "rb") as f:
        vs_file = client.vector_stores.files.upload_and_poll(
            vector_store_id=vs_id,
            file=(file_path.name, f),
        )

    meta = load_vector_store_meta()
    meta.setdefault("files", []).append(
        {"file_id": vs_file.id, "filename": file_path.name, "status": vs_file.status}
    )
    save_vector_store_meta(meta)
    return vs_file.id


def reset_vector_store():
    meta = load_vector_store_meta()
    vs_id = meta.get("vector_store_id")
    if vs_id:
        try:
            client.vector_stores.delete(vs_id)
        except Exception:
            pass
    if VECTOR_STORE_META.exists():
        VECTOR_STORE_META.unlink()


def build_agent(vector_store_id):
    return Agent(
        name="Life Coach",
        instructions="""
        당신은 따뜻하고 공감적인 라이프 코치입니다.
        사용자의 개인 목표와 일기 기록을 기억하고 이를 바탕으로 조언해주세요.

        - 진행상황/목표/습관/계획에 대한 조언을 할 때는 먼저 file_search로 사용자의
          목표·일기 문서를 반드시 확인하세요. 관련 부분을 짧게 인용해서 실제로
          문서를 참고했다는 걸 보여주세요.
        - 최신 연구나 구체적인 기법이 필요할 땐 web_search를 쓰세요.
        - file_search(사용자 본인 기록) + web_search(외부 정보) 조합으로
          막연한 격려 대신 구체적인 다음 행동을 제안해주세요.
        - 큰 목표는 작은 단계로 쪼개주세요.
        - 시간 흐름에 따른 변화를 물어보면 과거 일기 엔트리를 참고하세요.
        - 사용자가 쓰는 언어(한국어/영어)에 맞춰 답변하세요.
        """,
        tools=[
            FileSearchTool(
                vector_store_ids=[vector_store_id],
                include_search_results=True,
            ),
            WebSearchTool(),
        ],
    )


st.set_page_config(page_title="Life Coach — File Search", page_icon="🧭")
st.title("Life Coach Agent")
st.caption("파일 검색 + 웹 검색 + 세션 메모리를 결합한 라이프 코치")

if "vector_store_id" not in st.session_state:
    st.session_state["vector_store_id"] = ensure_vector_store()
vector_store_id = st.session_state["vector_store_id"]

if "agent" not in st.session_state:
    st.session_state["agent"] = build_agent(vector_store_id)
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "life-coach-session",
        str(APP_DIR / "life-coach-memory.db"),
    )
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                elif message.get("type") == "message":
                    st.write(message["content"][0]["text"])
        if message.get("type") == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔍 Searched the web...")
        if message.get("type") == "file_search_call":
            with st.chat_message("ai"):
                st.write("📂 Searched your goals/journal...")


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(agent, message, session=session)

        async for event in stream.stream_events():
            if event.type != "raw_response_event":
                continue
            et = event.data.type
            if et == "response.web_search_call.in_progress":
                status_container.update(label="🔍 Searching the web...", state="running")
            elif et == "response.web_search_call.completed":
                status_container.update(label="✅ Web search done.", state="complete")
            elif et == "response.file_search_call.in_progress":
                status_container.update(label="📂 Searching your goals/journal...", state="running")
            elif et == "response.file_search_call.completed":
                status_container.update(label="✅ File search done.", state="complete")
            elif et == "response.completed":
                status_container.update(label=" ", state="complete")
            elif et == "response.output_text.delta":
                response += event.data.delta
                text_placeholder.write(response)


prompt = st.chat_input("무엇이든 편하게 이야기해주세요...")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    st.header("Goals / Journal")
    meta = load_vector_store_meta()
    st.caption(f"Vector store: `{meta.get('vector_store_id', '-')}`")

    uploaded_files = st.file_uploader(
        "목표·일기 문서 업로드 (PDF/TXT/MD)",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Upload to vector store"):
        with st.spinner("Uploading & indexing..."):
            for uf in uploaded_files:
                dest = UPLOAD_DIR / uf.name
                dest.write_bytes(uf.getbuffer())
                upload_file_to_vector_store(vector_store_id, dest)
        st.success(f"{len(uploaded_files)}개의 문서를 인덱싱했습니다.")
        st.rerun()

    sample_path = APP_DIR / "my_goals.txt"
    if sample_path.exists():
        already = any(
            f.get("filename") == sample_path.name
            for f in load_vector_store_meta().get("files", [])
        )
        if not already and st.button("Load sample (my_goals.txt)"):
            with st.spinner("Indexing my_goals.txt..."):
                upload_file_to_vector_store(vector_store_id, sample_path)
            st.success("my_goals.txt를 인덱싱했습니다.")
            st.rerun()

    st.divider()
    st.subheader("Indexed files")
    files = meta.get("files", [])
    if not files:
        st.info("아직 업로드된 문서가 없습니다.")
    else:
        for f in files:
            st.write(f"• {f['filename']}")

    st.divider()
    st.header("Memory")
    if st.button("Reset conversation memory"):
        asyncio.run(session.clear_session())
        st.rerun()

    if st.button("Reset vector store"):
        reset_vector_store()
        for key in ("vector_store_id", "agent"):
            st.session_state.pop(key, None)
        st.rerun()
