from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import STORY_WRITER_DESCRIPTION, STORY_WRITER_PROMPT
from pydantic import BaseModel, Field
from typing import List


class PageOutput(BaseModel):
    page_number: int = Field(description="Page number, 1 through 5")
    text: str = Field(description="Page body text, written in Korean")
    visual_description: str = Field(
        description="Detailed English description for image generation"
    )


class StoryOutput(BaseModel):
    title: str = Field(description="Book title in Korean")
    theme: str = Field(description="The theme as understood from the user")
    pages: List[PageOutput] = Field(description="Exactly 5 pages")


MODEL = LiteLlm(model="openai/gpt-4o")

story_writer_agent = Agent(
    name="StoryWriterAgent",
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_PROMPT,
    model=MODEL,
    output_schema=StoryOutput,
    output_key="story",
)
