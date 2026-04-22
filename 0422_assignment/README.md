# Restaurant Bot (0421)

OpenAI Agents SDK의 handoff 기능을 사용한 레스토랑 봇입니다.
Triage Agent가 고객의 요청을 파악해서 Menu · Order · Reservation 중 맞는 전문 에이전트로 라우팅합니다.

## 에이전트 구성

| Agent | 역할 |
| --- | --- |
| **Triage Agent** | 고객의 의도 파악 후 전문 에이전트로 handoff |
| **Menu Agent** | 메뉴 / 재료 / 알레르기 / 채식·비건·글루텐프리 옵션 안내 |
| **Order Agent** | 주문 생성 · 아이템 추가 · 확정 · 총액 안내 |
| **Reservation Agent** | 예약 가능 여부 확인 · 예약 · 조회 · 취소 |

전문 에이전트끼리도 서로 handoff할 수 있어서 대화 중간에 주제를 바꿔도 자연스럽게 전환됩니다.
(예: 예약 중에 "채식 메뉴 있어요?" → Menu Agent로 handoff)

## 실행

```bash
cd 0421_assignment
uv sync
uv run streamlit run main.py
```

`.env` 파일에 `OPENAI_API_KEY=sk-...` 가 있어야 합니다.

> Dropbox 같은 클라우드 동기화 폴더에서 `uv sync`가 하드링크 오류(os error 396)로 실패하면 다음과 같이 복사 모드로 실행하세요:
> ```bash
> UV_LINK_MODE=copy uv sync --link-mode=copy
> ```

## 예시 상호작용

```
User: 예약을 하고 싶어
Triage: 예약 담당에게 연결해 드릴게요...
[Reservation Agent로 handoff]
Reservation: 예약을 도와드리겠습니다! 인원수와 희망 날짜·시간을 알려주세요.

User: 아, 그전에 채식 메뉴 있는지 알려줘
[Menu Agent로 handoff]
Menu: 네! Vegetable Bibimbap, Japchae, Tofu Salad 같은 채식 옵션이 있습니다...
```

## UI에서 확인할 수 있는 것

- **메인 채팅창**: `🔄 Triage Agent → Reservation Agent 로 연결합니다...`
- **사이드바**: 에이전트 활성화 / 도구 호출 / handoff 실시간 로그
- **현재 담당 에이전트**: 사이드바 상단에 항상 표시

## 파일 구조

```
0421_assignment/
├── main.py                      # Streamlit UI + 스트리밍 루프
├── models.py                    # CustomerContext, HandoffData, GuardRailOutput
├── tools.py                     # 메뉴 · 주문 · 예약 function_tool + AgentHooks
├── my_agents/
│   ├── triage_agent.py          # Triage + guardrail + make_handoff + 크로스 핸드오프 배선
│   ├── menu_agent.py
│   ├── order_agent.py
│   └── reservation_agent.py
├── pyproject.toml
└── README.md
```
