from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import InMemorySaver

from agents.classification_agent import classification_agent
from agents.tutor_agent import tutor_agent
from agents.quiz_agent import quiz_agent
from agents.researcher_agent import researcher_agent


class StudyMateState(MessagesState):
    current_agent: str


def router_check(state: StudyMateState):
    return state.get("current_agent", "classification_agent")


# 그래프 빌드
graph_builder = StateGraph(StudyMateState)

graph_builder.add_node(
    "classification_agent",
    classification_agent,
    destinations=("tutor_agent", "quiz_agent", "researcher_agent"),
)
graph_builder.add_node(
    "tutor_agent",
    tutor_agent,
    destinations=("quiz_agent", "classification_agent"),
)
graph_builder.add_node(
    "quiz_agent",
    quiz_agent,
    destinations=("researcher_agent", "classification_agent"),
)
graph_builder.add_node(
    "researcher_agent",
    researcher_agent,
    destinations=("quiz_agent", "classification_agent"),
)

# START → router_check → 해당 에이전트
graph_builder.add_conditional_edges(
    START,
    router_check,
    ["classification_agent", "tutor_agent", "quiz_agent", "researcher_agent"],
)

# 각 에이전트 → END (Command로 전환 시에는 END 대신 해당 에이전트로 점프)
graph_builder.add_edge("classification_agent", END)
graph_builder.add_edge("tutor_agent", END)
graph_builder.add_edge("quiz_agent", END)
graph_builder.add_edge("researcher_agent", END)

checkpointer = InMemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer, name="study_mate_multi")
