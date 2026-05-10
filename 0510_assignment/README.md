# StudyMate v2 — Education Agent Core Features (Day 2)

0506의 StudyMate(v1)에 **사용자 답안·점수 기반 분기**와 **웹검색 Tool 보강**을 추가한 버전.

## Weekend Mission 요구사항 매핑

| 요구사항 | 구현 위치 |
| --- | --- |
| **노드 3개+** | 8개 — `analyze_topic`, `make_flashcard`, `make_quiz`, `take_quiz`, `grade_quiz`, `summarize_well_done`, `search_concepts`, `review_explain` |
| **Conditional Edge** (사용자 입력에 따라 다른 경로) | `grade_quiz` → `route_by_score` (점수 ≥ 75% / < 75%로 분기) |
| **Tool 연동** | `DuckDuckGoSearchRun` (틀린 개념 보강 검색) |
| Send 병렬 (bonus) | `dispatch_cards` (5장), `dispatch_searches` (틀린 개념별) |
| 메모리 (bonus) | `InMemorySaver` checkpointer (interrupt resume용) |

## 파이프라인

```
START
  │
  ▼
analyze_topic         ── 핵심 개념 5개 (LLM)
  │ Send dispatch_cards
  ▼
make_flashcard × 5    ── 병렬 카드 생성
  │
  ▼
make_quiz             ── 객관식 4문제
  │
  ▼
take_quiz             ── interrupt()로 사용자 답안 받기
  │
  ▼
grade_quiz            ── 점수 계산 + 틀린 개념 추출
  │ ⭐ Conditional Edge (점수 기반)
  ├─ ≥ 75% ─▶ summarize_well_done ─▶ END
  └─ < 75% ─▶ search_concepts (Send) ─▶ review_explain ─▶ END
                  ↑ DuckDuckGo Tool 호출
```

## 사용자 흐름

1. 학습 주제 입력 → 핵심 개념 5개 + 플래시카드 5장 + 객관식 4문제 자동 생성
2. 콘솔에서 정답 인덱스 4개 콤마로 입력 (예: `0,2,1,3`)
3. **75% 이상**: 잘했어요 메시지로 종료
4. **75% 미만**: 틀린 개념마다 DuckDuckGo로 검색 → LLM이 학습자 친화적으로 재구성한 보강 설명 출력

## 파일

- `study_mate_v2.ipynb` — Day 2 구현 (Day 1은 0506_assignment/study_mate.ipynb)
- `pyproject.toml` — uv 의존성 (langchain-community, duckduckgo-search 추가)

## 실행

```bash
cd 0510_assignment
# .env에 OPENAI_API_KEY 입력
uv sync
uv run jupyter lab study_mate_v2.ipynb
```

## 다음 단계 (Day 3+)

- 보강 학습 후 다시 `make_quiz`로 루프 → 만점까지 반복
- 여러 Tool 추가 (Wikipedia, arXiv 등 학습 자료 다양화)
- 사용자 학습 history를 메모리에 누적해 약점 영역 분석
