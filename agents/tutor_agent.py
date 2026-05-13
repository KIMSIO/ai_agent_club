from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from tools.shared_tools import transfer_to_classification, web_search
from tools.quiz_tools import generate_flashcards

tutor_agent = create_react_agent(
    model=init_chat_model("openai:gpt-4o-mini"),
    tools=[web_search, generate_flashcards, transfer_to_classification],
    prompt="""당신은 튜터 에이전트입니다. 한국어로 응답합니다.

## 반드시 따를 절차:
1. web_search로 주제에 대한 정보를 검색합니다.
2. 검색 결과에서 핵심 개념 5개를 추출하여 사용자에게 보여줍니다.
3. generate_flashcards 도구를 호출합니다 (topic, concepts, research_text 모두 전달).

🚫 generate_flashcards를 호출하지 않고 직접 설명으로 대체하지 마세요.
🚫 web_search 없이 generate_flashcards를 호출하지 마세요.

generate_flashcards가 자동으로 퀴즈 단계로 넘어갑니다.
""",
    name="tutor_agent",
)
