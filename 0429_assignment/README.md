# Storybook Agent

테마를 받아 5페이지짜리 어린이 동화책을 만들어주는 두 에이전트.

- **StoryWriterAgent** — 테마를 받아 5페이지 분량의 이야기를 구조화된 JSON으로 작성하고, 결과를 `state["story"]`에 저장한다.
- **IllustratorAgent** — `state["story"]`에서 페이지를 읽고, 페이지마다 OpenAI `gpt-image-1`로 일러스트를 생성한 뒤 ADK Artifact로 저장한다.

두 에이전트는 `SequentialAgent`로 묶여 있다.

## 실행

```bash
cd 0429_assignment
# .env 파일에 OPENAI_API_KEY와 GOOGLE_API_KEY를 채운 뒤
uv sync
uv run adk web
```

브라우저에서 `storybook_agent`를 선택하고, 테마를 입력하면 된다.
예: `우정을 배우는 토끼 베니의 모험`
