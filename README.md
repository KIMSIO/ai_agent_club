# StudyMate v3 — 멀티 에이전트 + Streamlit UI

study_mate_v2의 단일 파이프라인을 멀티 에이전트 아키텍처로 리팩토링하고,
Streamlit 채팅 UI를 추가한 버전.

## 아키텍처

```
사용자 입력 → [분류 에이전트] → 의도 파악 후 라우팅
                    ↓
         ┌─────────┼─────────┐
         ↓         ↓         ↓
     [튜터]    [퀴즈]    [리서처]
     개념분석    퀴즈생성    웹검색
     카드생성    채점/피드백  보충설명
```

### 에이전트 구성

| 에이전트 | 역할 | 도구 |
|----------|------|------|
| 분류 에이전트 | 사용자 의도 파악, 라우팅 | transfer_to_* |
| 튜터 에이전트 | 핵심 개념 추출, 플래시카드 생성 | generate_flashcards, transfer_to_* |
| 퀴즈 에이전트 | 퀴즈 생성, 채점, 피드백 | generate_quiz, transfer_to_* |
| 리서처 에이전트 | 웹 검색, 보충 설명 | web_search, transfer_to_* |

### 고급 패턴

- **멀티 에이전트 아키텍처**: `create_react_agent` + `Command` 기반 에이전트 전환
- **구조화 출력**: Pydantic 모델로 퀴즈/플래시카드 생성
- **조건부 라우팅**: 퀴즈 점수(75%) 기준 통과/보강 분기

## 실행 방법

```bash
uv sync
uv run streamlit run app.py
```

## 기술 스택

- LangGraph (멀티 에이전트 오케스트레이션)
- LangChain + OpenAI (gpt-4o-mini)
- DuckDuckGo (웹 검색)
- Streamlit (채팅 UI)
- Pydantic (구조화 출력)
