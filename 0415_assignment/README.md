# 0415 — Life Coach + File Search

0414 과제(웹 검색 + 세션 메모리)에 File Search를 얹은 버전.

## 바뀐 점

- OpenAI Vector Store에 목표/일기 문서(PDF, TXT, MD) 업로드 → 인덱싱
- 에이전트에 `FileSearchTool` 추가, 조언 전에 항상 내 기록부터 검색하게 함
- `WebSearchTool`과 함께 써서 "내 기록 + 외부 정보" 조합으로 답변
- 사이드바에서 문서 업로드 / 샘플 로드 / vector store 초기화

## 파일

- `main.py` — Streamlit + Agent
- `my_goals.txt` — 내 목표/일기 샘플
- `.vector_store.json` — 생성된 vector store id (gitignore)
- `life-coach-memory.db` — SQLite 세션 메모리 (gitignore)

## 실행

```
uv sync
uv run streamlit run main.py
```

사이드바에서 `my_goals.txt` 올리거나 "Load sample" 버튼 누르고 질문하면 된다.
