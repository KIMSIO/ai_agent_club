from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.types import Command

_search = DuckDuckGoSearchRun()


# ── 에이전트 전환 도구 ──────────────────────────────────────


@tool
def transfer_to_tutor():
    """학습 주제 분석, 핵심 개념 추출, 플래시카드 생성이 필요할 때 튜터 에이전트로 전환합니다."""
    return Command(
        goto="tutor_agent",
        graph=Command.PARENT,
        update={"current_agent": "tutor_agent"},
    )


@tool
def transfer_to_quiz():
    """퀴즈 생성, 퀴즈 풀기, 채점이 필요할 때 퀴즈 에이전트로 전환합니다."""
    return Command(
        goto="quiz_agent",
        graph=Command.PARENT,
        update={"current_agent": "quiz_agent"},
    )


@tool
def transfer_to_researcher():
    """틀린 개념에 대한 추가 검색과 보충 설명이 필요할 때 리서처 에이전트로 전환합니다."""
    return Command(
        goto="researcher_agent",
        graph=Command.PARENT,
        update={"current_agent": "researcher_agent"},
    )


@tool
def transfer_to_classification():
    """사용자의 새로운 요청을 분류하기 위해 분류 에이전트로 돌아갑니다."""
    return Command(
        goto="classification_agent",
        graph=Command.PARENT,
        update={"current_agent": "classification_agent"},
    )


# ── 웹 검색 도구 ────────────────────────────────────────────


@tool
def web_search(query: str) -> str:
    """주어진 검색어로 웹 검색을 수행합니다. 학습 개념에 대한 추가 자료를 찾을 때 사용하세요.

    Args:
        query: 검색할 내용
    """
    try:
        result = _search.invoke(query)
        return result[:1500]
    except Exception as e:
        return f"검색 실패: {e}"
