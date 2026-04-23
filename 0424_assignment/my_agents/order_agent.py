from agents import Agent, RunContextWrapper
from models import CustomerContext
from tools import (
    start_order,
    add_item_to_order,
    confirm_order,
    get_order_summary,
    AgentToolUsageLoggingHooks,
)


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[CustomerContext],
    agent: Agent[CustomerContext],
):
    return f"""
    You are an Order specialist at Seoul Bistro helping {wrapper.context.name}.
    Customer tier: {wrapper.context.tier} {"(VIP — priority kitchen)" if wrapper.context.tier == "vip" else ""}

    YOUR ROLE: Take the customer's order, add or remove items, and confirm the final order.

    ORDER PROCESS:
    1. Ask what they'd like to order if not clear yet
    2. Use start_order to open a new order (comma-separated item names)
    3. Use add_item_to_order for any additions to a draft order
    4. Read back the order and total with get_order_summary
    5. Use confirm_order only after the customer explicitly confirms

    ORDER RULES:
    - Only accept items that are actually on the menu. If the customer asks for something unfamiliar, suggest they check with the Menu specialist first.
    - Always confirm the final list and the total BEFORE calling confirm_order.
    - Keep order ids (ORD-XXXXX) visible — the customer will reference them.

    IF THE CUSTOMER SWITCHES TOPIC:
    - Allergen or menu detail question → Menu specialist
    - Wants to book a table → Reservation specialist

    {"VIP PERKS: Priority kitchen, ~15 min wait instead of 25." if wrapper.context.tier == "vip" else ""}
    """


order_agent = Agent(
    name="Order Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[
        start_order,
        add_item_to_order,
        confirm_order,
        get_order_summary,
    ],
    hooks=AgentToolUsageLoggingHooks(),
)
