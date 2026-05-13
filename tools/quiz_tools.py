from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from pydantic import BaseModel, Field
from typing import Literal


# ── Pydantic 모델 ────────────────────────────────────────────


class Flashcard(BaseModel):
    concept: str = Field(description="개념 이름")
    question: str = Field(description="카드 앞면 질문")
    answer: str = Field(description="카드 뒷면 2~3문장 답변")


class FlashcardSet(BaseModel):
    cards: list[Flashcard] = Field(description="플래시카드 목록")


class QuizQuestion(BaseModel):
    question: str = Field(description="문제 텍스트")
    options: list[str] = Field(description="4개 선택지")
    answer_index: int = Field(description="정답 인덱스 (0~3)")
    concept: str = Field(description="이 문제가 묻는 개념")
    explanation: str = Field(description="정답이 맞는 이유와 나머지가 틀린 이유를 상세히 설명")


class Quiz(BaseModel):
    questions: list[QuizQuestion] = Field(description="퀴즈 문제 목록")


# ── 도구 ─────────────────────────────────────────────────────

_llm = init_chat_model("openai:gpt-4o-mini")


@tool
def generate_flashcards(topic: str, concepts: str, research_text: str):
    """웹 검색 결과를 기반으로 플래시카드를 생성하고, 자동으로 퀴즈 에이전트로 전환합니다.

    Args:
        topic: 학습 주제 (예: "FastAPI 의존성 주입")
        concepts: 쉼표로 구분된 개념 목록 (예: "의존성 주입, 선언형 경로, 비동기 함수")
        research_text: 웹 검색으로 수집한 참고 자료 텍스트
    """
    structured_llm = _llm.with_structured_output(FlashcardSet)
    result = structured_llm.invoke(
        f"주제: {topic}\n개념: {concepts}\n\n"
        f"아래 참고 자료를 기반으로 각 개념에 대해 정확한 학습용 플래시카드를 만들어주세요.\n"
        f"question은 핵심을 묻는 질문, answer는 2~3문장 한국어로 간결하게.\n"
        f"반드시 참고 자료의 사실에 기반하여 작성하세요.\n\n"
        f"<참고자료>\n{research_text}\n</참고자료>"
    )
    output = "📚 플래시카드\n\n"
    for i, card in enumerate(result.cards, 1):
        output += f"[{i}] {card.concept}\n"
        output += f"  Q. {card.question}\n"
        output += f"  A. {card.answer}\n\n"
    output += "이제 퀴즈로 이해도를 확인해볼게요!"

    return Command(
        goto="quiz_agent",
        graph=Command.PARENT,
        update={
            "current_agent": "quiz_agent",
            "messages": [AIMessage(content=output)],
        },
    )


@tool
def generate_quiz(
    research_text: str,
    topic: str,
    concepts: str,
    difficulty: Literal["easy", "medium", "hard"] = "medium",
    num_questions: int = 4,
) -> str:
    """웹 검색 결과를 기반으로 정확한 객관식 퀴즈를 생성합니다.

    Args:
        research_text: 웹 검색으로 수집한 참고 자료 텍스트 (필수!)
        topic: 학습 주제
        concepts: 쉼표로 구분된 개념 목록
        difficulty: 난이도 (easy, medium, hard)
        num_questions: 문제 수 (기본 4)
    """
    structured_llm = _llm.with_structured_output(Quiz)
    result = structured_llm.invoke(
        f"주제: {topic}\n개념: {concepts}\n난이도: {difficulty}\n\n"
        f"아래 참고 자료를 기반으로 객관식 {num_questions}문제를 만들어주세요.\n"
        f"각 문제는 4지선다이며, 정답 인덱스(0~3)와 상세한 설명을 포함합니다.\n"
        f"반드시 참고 자료의 사실에 기반하여 정확한 문제와 정답을 만드세요.\n"
        f"정답이 명확하지 않은 문제는 만들지 마세요.\n\n"
        f"<참고자료>\n{research_text}\n</참고자료>"
    )
    output = f"📝 퀴즈 ({len(result.questions)}문제)\n\n"
    for i, q in enumerate(result.questions, 1):
        output += f"[{i}] {q.question}\n"
        for j, opt in enumerate(q.options):
            output += f"   {j}) {opt}\n"
        output += "\n"
    output += "✏️ 정답 인덱스(0~3)를 콤마로 구분해서 입력해주세요. 예: 0,2,1,3\n"

    # 채점용 데이터를 포함 (에이전트가 참조)
    answer_key = ",".join(str(q.answer_index) for q in result.questions)
    concepts_key = "|".join(q.concept for q in result.questions)
    explanations = "|".join(q.explanation for q in result.questions)
    output += f"\n[ANSWER_KEY:{answer_key}]"
    output += f"\n[CONCEPTS_KEY:{concepts_key}]"
    output += f"\n[EXPLANATIONS:{explanations}]"
    return output


PASS_THRESHOLD = 0.75


@tool
def grade_quiz(answer_key: str, user_answers: str, concepts_key: str, explanations: str):
    """퀴즈를 채점하고 점수에 따라 자동으로 다음 에이전트로 전환합니다.
    채점 후 75% 이상이면 분류 에이전트로, 미만이면 리서처 에이전트로 이동합니다.

    Args:
        answer_key: ANSWER_KEY 값, 쉼표 구분 (예: "3,2,0,1")
        user_answers: 사용자 답안, 쉼표 구분 (예: "1,3,3,3")
        concepts_key: CONCEPTS_KEY 값, 파이프 구분
        explanations: EXPLANATIONS 값, 파이프 구분
    """
    correct_list = [x.strip() for x in answer_key.split(",")]
    user_list = [x.strip() for x in user_answers.split(",")]
    concept_list = [x.strip() for x in concepts_key.split("|")]
    expl_list = [x.strip() for x in explanations.split("|")]

    correct_count = 0
    wrong_concepts = []
    feedback_lines = []

    for i, (correct_a, user_a) in enumerate(zip(correct_list, user_list)):
        concept = concept_list[i] if i < len(concept_list) else ""
        expl = expl_list[i] if i < len(expl_list) else ""
        if correct_a == user_a:
            correct_count += 1
            feedback_lines.append(f"[{i+1}] ✓ 정답 ({concept})")
        else:
            wrong_concepts.append(concept)
            feedback_lines.append(f"[{i+1}] ✗ 오답 (정답: {correct_a}) — {expl}")

    total = len(correct_list)
    score = correct_count / total if total > 0 else 0
    feedback = "\n".join(feedback_lines)

    result_msg = f"📊 점수: {correct_count}/{total} ({score*100:.0f}%)\n\n{feedback}"

    if score >= PASS_THRESHOLD:
        result_msg += "\n\n🎉 잘했어요! 새로운 주제를 학습해볼까요?"
        return Command(
            goto="classification_agent",
            graph=Command.PARENT,
            update={
                "current_agent": "classification_agent",
                "messages": [AIMessage(content=result_msg)],
            },
        )
    else:
        result_msg += f"\n\n📚 틀린 개념({', '.join(wrong_concepts)})에 대해 보충 학습을 시작합니다..."
        return Command(
            goto="researcher_agent",
            graph=Command.PARENT,
            update={
                "current_agent": "researcher_agent",
                "messages": [AIMessage(content=result_msg)],
            },
        )
