import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import CustomerContext
import random
from datetime import datetime


# =============================================================================
# MENU DATA
# =============================================================================


MENU = {
    "appetizers": [
        {
            "name": "Kimchi Pancake",
            "price": 12.0,
            "description": "Crispy pancake with aged kimchi and scallions.",
            "allergens": ["gluten", "egg"],
            "tags": ["vegetarian"],
        },
        {
            "name": "Tofu Salad",
            "price": 10.0,
            "description": "Warm tofu with sesame vinaigrette and seasonal greens.",
            "allergens": ["soy", "sesame"],
            "tags": ["vegetarian", "vegan", "gluten-free"],
        },
        {
            "name": "Shrimp Mandu",
            "price": 14.0,
            "description": "Steamed dumplings stuffed with shrimp and chive.",
            "allergens": ["gluten", "shellfish"],
            "tags": [],
        },
    ],
    "mains": [
        {
            "name": "Bibimbap",
            "price": 18.0,
            "description": "Rice bowl with seasonal vegetables, beef, and gochujang.",
            "allergens": ["soy", "egg", "sesame"],
            "tags": [],
        },
        {
            "name": "Vegetable Bibimbap",
            "price": 16.0,
            "description": "Rice bowl with seasonal vegetables and gochujang, no meat.",
            "allergens": ["soy", "egg", "sesame"],
            "tags": ["vegetarian"],
        },
        {
            "name": "Galbi",
            "price": 32.0,
            "description": "Marinated grilled short ribs with rice and banchan.",
            "allergens": ["soy", "sesame"],
            "tags": [],
        },
        {
            "name": "Japchae",
            "price": 17.0,
            "description": "Sweet potato glass noodles stir-fried with vegetables.",
            "allergens": ["soy", "sesame"],
            "tags": ["vegetarian", "vegan", "gluten-free"],
        },
    ],
    "desserts": [
        {
            "name": "Hotteok",
            "price": 7.0,
            "description": "Pan-fried sweet pancake with brown sugar and nuts.",
            "allergens": ["gluten", "peanut", "tree nut"],
            "tags": ["vegetarian"],
        },
        {
            "name": "Patbingsu",
            "price": 12.0,
            "description": "Shaved ice with sweet red bean, rice cake, and condensed milk.",
            "allergens": ["milk"],
            "tags": ["vegetarian", "gluten-free"],
        },
    ],
}


# =============================================================================
# ORDER / RESERVATION STATE (in-memory for demo)
# =============================================================================


ORDERS: dict[str, dict] = {}
RESERVATIONS: dict[str, dict] = {}


def _format_menu_item(item: dict) -> str:
    tag_str = f" [{', '.join(item['tags'])}]" if item["tags"] else ""
    return f"• {item['name']} — ${item['price']:.2f}{tag_str}\n  {item['description']}"


def _find_item(name: str) -> dict | None:
    q = name.lower().strip()
    for category in MENU.values():
        for item in category:
            if item["name"].lower() == q:
                return item
    return None


# =============================================================================
# MENU TOOLS
# =============================================================================


@function_tool
def get_full_menu(context: RunContextWrapper[CustomerContext]) -> str:
    """Return the entire menu grouped by category."""
    lines = ["🍽️ Seoul Bistro Menu"]
    for category, items in MENU.items():
        lines.append(f"\n— {category.upper()} —")
        for item in items:
            lines.append(_format_menu_item(item))
    return "\n".join(lines)


@function_tool
def get_menu_by_category(
    context: RunContextWrapper[CustomerContext], category: str
) -> str:
    """
    Return menu items for a specific category.

    Args:
        category: Category name (appetizers, mains, desserts)
    """
    items = MENU.get(category.lower().strip())
    if not items:
        available = ", ".join(MENU.keys())
        return f"❌ Unknown category '{category}'. Available: {available}"
    lines = [f"🍽️ {category.title()}"]
    for item in items:
        lines.append(_format_menu_item(item))
    return "\n".join(lines)


@function_tool
def check_allergens(
    context: RunContextWrapper[CustomerContext], item_name: str
) -> str:
    """
    Check the allergens in a specific menu item.

    Args:
        item_name: Exact name of the menu item
    """
    item = _find_item(item_name)
    if not item:
        return f"❌ Could not find '{item_name}' on the menu."
    if not item["allergens"]:
        return f"✅ {item['name']} contains no common allergens."
    return f"⚠️ {item['name']} contains: {', '.join(item['allergens'])}"


@function_tool
def find_dietary_options(
    context: RunContextWrapper[CustomerContext], diet: str
) -> str:
    """
    Find menu items matching a dietary preference.

    Args:
        diet: Dietary tag (vegetarian, vegan, gluten-free)
    """
    tag = diet.lower().strip()
    matches = []
    for items in MENU.values():
        for item in items:
            if tag in item["tags"]:
                matches.append(_format_menu_item(item))
    if not matches:
        return f"😔 No {tag} items found."
    return f"🌱 {tag.title()} options:\n" + "\n".join(matches)


# =============================================================================
# ORDER TOOLS
# =============================================================================


@function_tool
def start_order(
    context: RunContextWrapper[CustomerContext], items: str
) -> str:
    """
    Start a new order with the given items.

    Args:
        items: Comma-separated list of menu item names
    """
    requested = [name.strip() for name in items.split(",") if name.strip()]
    order_id = f"ORD-{random.randint(10000, 99999)}"
    resolved, missing, total = [], [], 0.0
    for name in requested:
        item = _find_item(name)
        if item is None:
            missing.append(name)
        else:
            resolved.append(item)
            total += item["price"]

    ORDERS[order_id] = {
        "customer_id": context.context.customer_id,
        "items": resolved,
        "total": total,
        "status": "draft",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    lines = [f"🧾 Order {order_id} started"]
    for item in resolved:
        lines.append(f"• {item['name']} — ${item['price']:.2f}")
    if missing:
        lines.append(f"⚠️ Not on menu: {', '.join(missing)}")
    lines.append(f"Subtotal: ${total:.2f}")
    return "\n".join(lines)


@function_tool
def add_item_to_order(
    context: RunContextWrapper[CustomerContext],
    order_id: str,
    item_name: str,
) -> str:
    """
    Add a single item to an existing draft order.

    Args:
        order_id: Order id returned from start_order
        item_name: Menu item name to add
    """
    order = ORDERS.get(order_id)
    if not order:
        return f"❌ Order {order_id} not found."
    if order["status"] != "draft":
        return f"❌ Order {order_id} is already {order['status']}."
    item = _find_item(item_name)
    if not item:
        return f"❌ '{item_name}' is not on the menu."
    order["items"].append(item)
    order["total"] += item["price"]
    return f"✅ Added {item['name']} to {order_id}. New subtotal: ${order['total']:.2f}"


@function_tool
def confirm_order(
    context: RunContextWrapper[CustomerContext], order_id: str
) -> str:
    """
    Confirm and finalize an order.

    Args:
        order_id: Order id to confirm
    """
    order = ORDERS.get(order_id)
    if not order:
        return f"❌ Order {order_id} not found."
    if order["status"] == "confirmed":
        return f"ℹ️ Order {order_id} was already confirmed."
    order["status"] = "confirmed"
    wait = 15 if context.context.tier == "vip" else 25
    return f"""
✅ Order {order_id} confirmed
💰 Total: ${order['total']:.2f}
⏱️ Estimated wait: {wait} minutes
🙏 Thank you, {context.context.name}.
    """.strip()


@function_tool
def get_order_summary(
    context: RunContextWrapper[CustomerContext], order_id: str
) -> str:
    """
    Return the current summary of an order.

    Args:
        order_id: Order id to look up
    """
    order = ORDERS.get(order_id)
    if not order:
        return f"❌ Order {order_id} not found."
    lines = [f"🧾 Order {order_id} ({order['status']})"]
    for item in order["items"]:
        lines.append(f"• {item['name']} — ${item['price']:.2f}")
    lines.append(f"Total: ${order['total']:.2f}")
    return "\n".join(lines)


# =============================================================================
# RESERVATION TOOLS
# =============================================================================


@function_tool
def check_availability(
    context: RunContextWrapper[CustomerContext],
    date: str,
    time: str,
    party_size: int,
) -> str:
    """
    Check whether a table is available for the given date and time.

    Args:
        date: Reservation date in YYYY-MM-DD
        time: Reservation time in 24h HH:MM
        party_size: Number of guests
    """
    if party_size > 10:
        return f"❌ Parties larger than 10 need to call us directly."
    seed = hash((date, time)) % 5
    slots = max(0, 4 - seed)
    if slots == 0:
        return f"😔 {date} {time} is fully booked. Try an hour earlier or later."
    return f"✅ {slots} table(s) available on {date} at {time} for {party_size} guests."


@function_tool
def make_reservation(
    context: RunContextWrapper[CustomerContext],
    date: str,
    time: str,
    party_size: int,
    special_request: str = "",
) -> str:
    """
    Book a table reservation.

    Args:
        date: Reservation date in YYYY-MM-DD
        time: Reservation time in 24h HH:MM
        party_size: Number of guests
        special_request: Optional note (window seat, birthday, allergies)
    """
    reservation_id = f"RES-{random.randint(10000, 99999)}"
    RESERVATIONS[reservation_id] = {
        "customer_id": context.context.customer_id,
        "name": context.context.name,
        "date": date,
        "time": time,
        "party_size": party_size,
        "special_request": special_request,
        "status": "confirmed",
    }
    return f"""
📅 Reservation confirmed
🔗 Reservation ID: {reservation_id}
👤 Name: {context.context.name}
📆 {date} at {time}
👥 Party of {party_size}
📝 Note: {special_request or 'None'}
    """.strip()


@function_tool
def lookup_reservation(
    context: RunContextWrapper[CustomerContext], reservation_id: str
) -> str:
    """
    Look up an existing reservation.

    Args:
        reservation_id: Reservation id
    """
    res = RESERVATIONS.get(reservation_id)
    if not res:
        return f"❌ Reservation {reservation_id} not found."
    return f"""
📅 Reservation {reservation_id} ({res['status']})
👤 {res['name']} — party of {res['party_size']}
📆 {res['date']} at {res['time']}
📝 {res['special_request'] or 'No special request'}
    """.strip()


@function_tool
def cancel_reservation(
    context: RunContextWrapper[CustomerContext], reservation_id: str
) -> str:
    """
    Cancel an existing reservation.

    Args:
        reservation_id: Reservation id to cancel
    """
    res = RESERVATIONS.get(reservation_id)
    if not res:
        return f"❌ Reservation {reservation_id} not found."
    res["status"] = "cancelled"
    return f"✅ Reservation {reservation_id} cancelled. Hope to see you another time, {context.context.name}."


# =============================================================================
# HOOKS
# =============================================================================


class AgentToolUsageLoggingHooks(AgentHooks):

    async def on_tool_start(
        self,
        context: RunContextWrapper[CustomerContext],
        agent: Agent[CustomerContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** starting tool: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[CustomerContext],
        agent: Agent[CustomerContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** used tool: `{tool.name}`")
            st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[CustomerContext],
        agent: Agent[CustomerContext],
        source: Agent[CustomerContext],
    ):
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** → **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[CustomerContext],
        agent: Agent[CustomerContext],
    ):
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** activated")

    async def on_end(
        self,
        context: RunContextWrapper[CustomerContext],
        agent: Agent[CustomerContext],
        output,
    ):
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** completed")
