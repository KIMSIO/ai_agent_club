# StudyMate (v1 — 데모 데이 Day 1)

학습 주제 한 줄을 입력하면, **핵심 개념 정리 → 플래시카드 → 객관식 퀴즈**를 한 번에 만들어주는 자기주도 학습 도우미.

## 왜 만드는가

시험 준비할 때 매번 직접 정리 → 카드 만들기 → 문제 풀어보기 사이클을 돌리는데,
이 중에서 "정리하고 카드 만드는 단계"가 너무 시간을 잡아먹는다.
LLM이 한 방에 만들어주면 학습자는 **회상(recall)** 과 **검증(quiz)** 에만 집중하면 된다.

## 파이프라인

```
[입력: "FastAPI 의존성 주입"]
        │
        ▼
   analyze_topic        — 핵심 개념 5개 추출
        │
        ▼
  (dispatch_cards) ── Send ──┐
                             ▼
                     make_flashcard × 5  (병렬)
                             │
                             ▼
                        make_quiz        — 객관식 4문제
                             │
                             ▼
                            END
```

## 핵심 기능

1. **개념 추출** — 주제 → 학습 포인트 5개 (LLM 1회 호출)
2. **플래시카드 생성** — 각 개념별 Q&A 카드, `Send`로 5장 동시 생성
3. **이해도 퀴즈** — 5개 개념을 묶어 객관식 4문제 + 정답 인덱스

## 파일

- `study_mate.ipynb` — 설계 문서 + LangGraph 구현 + 실행 결과
- `pyproject.toml` — uv 의존성

## 실행

```bash
cd 0506_assignment
# .env에 OPENAI_API_KEY 입력
uv sync
uv run jupyter lab study_mate.ipynb
```

## 다음 단계 (Day 2 이후)

- 사용자가 카드 보고 "어려움/쉬움" 표시 → 어려운 개념만 다시 카드 보강
- 퀴즈 채점 후 틀린 문제 개념만 추출해 추가 학습 루프
- `interrupt()`로 인터랙티브 학습 세션 (강의 #15.5에서 본 패턴)
