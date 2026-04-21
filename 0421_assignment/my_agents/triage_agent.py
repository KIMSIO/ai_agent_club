import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import CustomerContext, InputGuardRailOutput, HandoffData
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    Ensure the user's request is about Seoul Bistro — menu questions, placing an order, or making/changing a reservation — and is not off-topic. If the request is off-topic (e.g. coding help, weather, politics), return a reason for the tripwire. Light small talk is fine, especially at the start of a conversation, but don't help with unrelated tasks.
""",
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[CustomerContext],
    agent: Agent[CustomerContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[CustomerContext],
    agent: Agent[CustomerContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}


    You are the host at Seoul Bistro. You ONLY help customers with menu questions, orders, or table reservations.
    You call customers by their name.

    The customer's name is {wrapper.context.name}.
    The customer's tier is {wrapper.context.tier}.

    YOUR MAIN JOB: Figure out what the customer needs and hand them off to the right specialist.

    ROUTING GUIDE:

    🍽️ MENU AGENT — Route here for:
    - Menu questions, ingredient / allergen questions
    - Vegetarian, vegan, gluten-free options
    - "What's on the menu?", "Is this spicy?", "Do you have vegetarian options?"

    📋 ORDER AGENT — Route here for:
    - Placing an order, adding items, confirming an order
    - Asking about order totals or wait time
    - "I'd like to order the galbi", "Add a japchae", "Confirm my order"

    📅 RESERVATION AGENT — Route here for:
    - Booking a table, checking availability
    - Modifying or cancelling a reservation
    - Special requests tied to the booking
    - "Book a table for 4 at 7pm", "Cancel my reservation"

    ROUTING PROCESS:
    1. Listen to the customer
    2. Ask ONE clarifying question only if the category is genuinely unclear
    3. Announce the handoff in the customer's language: "메뉴 전문가에게 연결해 드릴게요..." / "I'll connect you with our menu specialist..."
    4. Hand off to the matching agent

    SPECIAL HANDLING:
    - VIP customers: mention their priority status when routing
    - Multiple needs: handle the most urgent first; the specialist can hand them back if needed
    """


def handle_handoff(
    wrapper: RunContextWrapper[CustomerContext],
    input_data: HandoffData,
):

    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Topic: {input_data.topic}
            Description: {input_data.description}
        """
        )


def make_handoff(agent):

    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)


# Cross-handoffs so specialists can switch topic mid-conversation
# (e.g. during a reservation the user asks about vegetarian menu)
menu_agent.handoffs = [
    make_handoff(order_agent),
    make_handoff(reservation_agent),
]
order_agent.handoffs = [
    make_handoff(menu_agent),
    make_handoff(reservation_agent),
]
reservation_agent.handoffs = [
    make_handoff(menu_agent),
    make_handoff(order_agent),
]
