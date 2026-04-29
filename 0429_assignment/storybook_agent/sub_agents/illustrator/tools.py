import base64
from google.genai import types
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext

client = OpenAI()


# A single, consistent style suffix appended to every page prompt so that all
# 5 illustrations look like they belong to the same book.
STYLE_SUFFIX = (
    "soft watercolor children's book illustration, warm pastel palette, "
    "gentle lighting, square 1:1 framing, no text, no letters"
)


async def generate_illustrations(tool_context: ToolContext):
    """Generate one illustration per page of the story sitting in state['story'].

    Reads the structured story written by StoryWriterAgent, calls gpt-image-1
    once per page, and saves each result as an ADK artifact named
    `page_{n}.png`. Skips pages that have already been generated in this
    session so that retries are cheap.
    """

    story = tool_context.state.get("story")
    if not story:
        return {
            "status": "error",
            "message": "No story found in state. StoryWriterAgent must run first.",
        }

    title = story.get("title")
    pages = story.get("pages", [])

    existing_artifacts = await tool_context.list_artifacts()

    generated = []

    for page in pages:
        page_number = page.get("page_number")
        visual = page.get("visual_description")
        filename = f"page_{page_number}.png"

        if filename in existing_artifacts:
            generated.append({"page_number": page_number, "filename": filename, "skipped": True})
            continue

        full_prompt = f"{visual}. {STYLE_SUFFIX}"

        image = client.images.generate(
            model="gpt-image-1",
            prompt=full_prompt,
            n=1,
            size="1024x1024",
            quality="low",
            moderation="low",
            output_format="png",
            background="opaque",
        )

        image_bytes = base64.b64decode(image.data[0].b64_json)

        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="image/png",
                data=image_bytes,
            )
        )

        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )

        generated.append({"page_number": page_number, "filename": filename, "skipped": False})

    return {
        "status": "complete",
        "title": title,
        "total_pages": len(generated),
        "pages": generated,
    }
