from pydantic import BaseModel
from typing import Optional


class CustomerContext(BaseModel):

    customer_id: int
    name: str
    tier: str = "regular"  # regular, vip
    phone: Optional[str] = None


class InputGuardRailOutput(BaseModel):

    is_off_topic: bool
    reason: str


class HandoffData(BaseModel):

    to_agent_name: str
    topic: str
    description: str
    reason: str
