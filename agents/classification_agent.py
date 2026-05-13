from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from tools.shared_tools import transfer_to_tutor, transfer_to_quiz, transfer_to_researcher

classification_agent = create_react_agent(
    model=init_chat_model("openai:gpt-4o-mini"),
    tools=[transfer_to_tutor, transfer_to_quiz, transfer_to_researcher],
    prompt="""당신은 분류 에이전트입니다. 한국어로 응답합니다.

## 최우선 규칙 (절대 어기지 마세요):
당신은 학습 내용을 직접 설명하지 않습니다.
사용자가 주제를 말하면, 즉시 transfer_to_tutor를 호출하세요.

## 라우팅:
- 주제를 공부하고 싶다 → transfer_to_tutor
- 퀴즈를 풀고 싶다 → transfer_to_quiz
- 개념을 더 검색하고 싶다 → transfer_to_researcher
""",
    name="classification_agent",
)
