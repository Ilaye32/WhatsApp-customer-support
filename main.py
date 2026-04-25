import os
import sys
import asyncio
from dotenv import load_dotenv

from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.store.mongodb.base import MongoDBStore, VectorIndexConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, MessagesState
from langchain.agents.middleware import before_model
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from tools import firecrawler, knowledgebase, web_crawler, analyze_image

load_dotenv()






# ========================= CONFIG =========================

MONGODB_URL = os.getenv("MONGO_DB_URL")

client = MongoClient(MONGODB_URL)
db = client["memories"]
collection = db["memory_store"]

store = MongoDBStore(
    collection=collection,
    index_config=VectorIndexConfig(
        fields=None,
        filters=None,
        dims=3072,  
        embed=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    ),
    auto_index_timeout=70
)

checkpointer = MongoDBSaver(
    client,
    db_name="memories",
    collection_name="thread_checkpoints"
)


llm_model = ChatOpenAI(
    temperature=1.0,
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    timeout=300,          
    streaming=True,
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing. Add it to your .env file.")

SYSTEM_PROMPT = """Your system prompt here"""

async def run_agent(
    user_message: str,
    from_number: str,
    image_bytes: bytes = None,
    mime_type: str = None,
) -> str:
    # --- Image analysis (Gemini) ---
    if image_bytes is not None:
        print("Analyzing image with Gemini before passing to agent...")
        image_description = analyze_image.invoke({
            "image_bytes": image_bytes,
            "mime_type": mime_type or "image/jpeg"
        })
        user_message = (
            f"[Image Analysis]\n{image_description}\n\n"
            f"[User's message about the image]\n{user_message}"
        )
        print(f"Image analyzed. Description: {len(image_description)} chars")

    # --- Agent always runs (image or text) ---
    config = {"configurable": {"thread_id": from_number}}
    agent = create_agent(
    model=llm_model,
    tools=[firecrawler, knowledgebase, web_crawler],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
     )
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )

    return result["messages"][-1].content

# ========================= MAIN LOOP =========================
async def main_loop():
    from_number = "12222"   # In production, use real WhatsApp/Telegram number

    while True:
        try:
            user_input = input("User: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                print("Goodbye!")
                break

            response = await run_agent(user_input, from_number)
            print("Ella:", response)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main_loop())
