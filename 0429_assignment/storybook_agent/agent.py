from google.adk.agents import SequentialAgent
from .sub_agents.story_writer.agent import story_writer_agent
from .sub_agents.illustrator.agent import illustrator_agent

storybook_agent = SequentialAgent(
    name="StorybookAgent",
    description=(
        "Turns a theme into a 5-page illustrated children's storybook. "
        "First the StoryWriter writes the book and parks it in state, "
        "then the Illustrator renders one image per page."
    ),
    sub_agents=[
        story_writer_agent,
        illustrator_agent,
    ],
)

root_agent = storybook_agent
