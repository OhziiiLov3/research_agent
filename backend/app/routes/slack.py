from fastapi import APIRouter, Form
from app.services.agent import research_agent
import asyncio
from slack_sdk import WebClient
import os

router = APIRouter()
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# -------------------------------
# Helper: Post threaded response
# -------------------------------
async def post_research_thread(channel_id, user_id, query_text):
    try:
        # Run agent in a separate thread
        answer, observations = await asyncio.to_thread(research_agent, query_text, [], False)
        # print("DEBUG >> agent output:", answer, observations)

        # Post placeholder first to start thread
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Research in progress..."
        )
        thread_ts = placeholder["ts"]

        # Post final answer in the thread
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            thread_ts=thread_ts,
            text=answer
        )

    except Exception as e:
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Error running research: {str(e)}"
        )


# -------------------------------
# Slack Slash Command Endpoint
# -------------------------------

@router.post("/slack/research")
async def slack_research(
    text: str = Form(...), 
    user_id: str = Form(...), 
    channel_id: str = Form(...)
):
    # 1️⃣ Respond immediately
    ephemeral_response = {
        "response_type": "ephemeral",
        "text": f"Got it! Running research for: {text}"
    }

    # 2️⃣ Trigger background task for final answer
    asyncio.create_task(post_research_thread(channel_id, user_id, text))

    return ephemeral_response

# @router.post("/slack/research")
# async def slack_research(
#     text: str = Form(...), 
#     user_id: str = Form(...), 
#     channel_id: str = Form(...)
# ):
#     # Trigger the async thread function
#     asyncio.create_task(post_research_thread(channel_id, user_id, text))

#     # Respond ephemeral immediately
#     return {"response_type": "ephemeral", "text": f"Running research for: {text}"}
