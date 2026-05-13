from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from tools.shared_tools import web_search
from tools.quiz_tools import generate_quiz, grade_quiz

quiz_agent = create_react_agent(
    model=init_chat_model("openai:gpt-4o-mini"),
    tools=[web_search, generate_quiz, grade_quiz],
    prompt="""당신은 퀴즈 에이전트입니다. 한국어로 응답합니다.

## 퀴즈 생성 절차:
1. web_search로 주제를 검색합니다.
2. generate_quiz 도구를 호출합니다 (research_text에 검색 결과 전달).
3. 사용자 답안을 기다립니다.

## 채점 절차 (⚠️ 반드시 따르세요):
사용자가 답안(예: "1,3,3,3")을 입력하면, 반드시 grade_quiz 도구를 호출하세요.
- answer_key: 퀴즈의 [ANSWER_KEY:...] 값
- user_answers: 사용자가 입력한 답안
- concepts_key: 퀴즈의 [CONCEPTS_KEY:...] 값
- explanations: 퀴즈의 [EXPLANATIONS:...] 값

🚫 직접 채점하지 마세요. 반드시 grade_quiz 도구를 사용하세요.
grade_quiz가 자동으로 다음 단계를 처리합니다.
""",
    name="quiz_agent",
)
