# core/relevance_analyzer.py
import asyncio
from llm_call import chat_completion_async

async def analyze_relevance_async(description: str, sem: asyncio.Semaphore, base_prompt: str):
    """
    Analyze relevance of a feed item using the provided LLM prompt.
    Each feed can have its own unique base_prompt.
    """
    question = f"{base_prompt}\n\nTEXT:\n{description}"

    chat_history = [
        {
            "role": "system",
            "content": "You are a precise and concise news analyst. Output must conform to the schema: score (integer), reasoning (text).",
        },
        {"role": "user", "content": question},
    ]

    async with sem:
        return await chat_completion_async(
            chat_history=chat_history, temperature=0.2, use_structured=True
        )
