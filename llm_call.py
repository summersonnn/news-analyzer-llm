import os
import asyncio
import time
import random
from typing import List, Dict, Union
from openai import OpenAI, AsyncOpenAI

# NEW: instructor + pydantic for structured outputs
import instructor
from pydantic import BaseModel

# Retry constants
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # seconds


# NEW: Structured output model (exactly two fields)
class Evaluation(BaseModel):
    score: int          # e.g., 1..10
    reasoning: str      # free-form explanation

async def chat_completion_async(
    chat_history: List[Dict[str, str]],
    temperature: float = 0.5,
    use_structured: bool = False,  # If True, return Evaluation(score:int, reasoning:str)
) -> Union[str, "Evaluation"]:
    """
    Async LLM chat completion helper using openai/gpt-5-mini with retries.
    If use_structured=True, returns an Evaluation via instructor JSON schema enforcement.
    """

    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")

    if not base_url:
        raise AttributeError("LLM_BASE_URL environment variable not set.")
    if not api_key:
        raise AttributeError("LLM_API_KEY environment variable not set.")

    # Create async OpenAI client
    client: AsyncOpenAI | instructor.Client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url.rstrip('/'),
    )

    # If structured mode is requested, patch client for JSON schema enforcement
    if use_structured:
        client = instructor.from_openai(client, mode=instructor.Mode.JSON)

    model_name = "openai/gpt-5-mini"

    request_params: Dict = {
        "model": model_name,
        "messages": chat_history.copy(),
        "temperature": temperature,
        "max_tokens": 1024,
    }

    # In structured mode, instruct the client to parse into our Evaluation model
    if use_structured:
        request_params["response_model"] = Evaluation  # type: ignore[name-defined]

    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            # IMPORTANT: await the async create call
            response = await client.chat.completions.create(**request_params)

            # In structured mode, response is already an Evaluation instance
            if use_structured:
                return response  # type: ignore[return-value]

            # Non-structured: return raw text
            return response.choices[0].message.content  # type: ignore[union-attr]

        except Exception as e:
            last_exception = e
            attempt_num = attempt + 1
            print(f"Error during chat completion on attempt {attempt_num}/{MAX_RETRIES}: {e}")

            if attempt < MAX_RETRIES - 1:
                # Exponential backoff with jitter
                delay = (RETRY_DELAY_SECONDS * (2 ** attempt)) + random.uniform(0, 0.5)
                print(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
            else:
                print(f"All {MAX_RETRIES} retry attempts failed for model {model_name}.")
                raise e

    # Should never reach here
    raise RuntimeError(f"Chat completion failed unexpectedly. Last error: {last_exception}")


# def chat_completion(
#     chat_history: List[Dict[str, str]],
#     temperature: float = 0.5,
#     use_structured: bool = False,  # NEW: toggle structured output
# ) -> Union[str, Evaluation]:
#     """
#     Simple LLM chat completion helper using openai/gpt-5-mini with retries.
#     If use_structured=True, returns an Evaluation(score:int, reasoning:str)
#     using the instructor package to enforce the schema.
#     """

#     load_dotenv()

#     base_url = os.getenv("LLM_BASE_URL")
#     api_key = os.getenv("LLM_API_KEY")

#     if not base_url:
#         raise AttributeError("LLM_BASE_URL environment variable not set.")
#     if not api_key:
#         raise AttributeError("LLM_API_KEY environment variable not set.")

#     # Create OpenAI client
#     client = OpenAI(api_key=api_key, base_url=base_url.rstrip('/'))

#     # If structured mode is requested, patch client for JSON schema enforcement
#     if use_structured:
#         client = instructor.from_openai(client, mode=instructor.Mode.JSON)

#     model_name = "openai/gpt-5-mini"

#     request_params = {
#         "model": model_name,
#         "messages": chat_history.copy(),
#         "temperature": temperature,
#         "max_tokens": 1024,
#     }

#     # In structured mode, instruct the client to parse into our Evaluation model
#     if use_structured:
#         request_params["response_model"] = Evaluation

#     last_exception = None
#     for attempt in range(MAX_RETRIES):
#         try:
#             response = client.chat.completions.create(**request_params)

#             # In structured mode, response is already an Evaluation instance
#             if use_structured:
#                 return response  # type: Evaluation

#             # In non-structured mode, keep original string behavior
#             return response.choices[0].message.content

#         except Exception as e:
#             last_exception = e
#             print(f"Error during chat completion on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
#             if attempt < MAX_RETRIES - 1:
#                 print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
#                 time.sleep(RETRY_DELAY_SECONDS)
#             else:
#                 print(f"All {MAX_RETRIES} retry attempts failed for model {model_name}.")
#                 raise e

#     raise RuntimeError("Chat completion failed unexpectedly.")


async def main():
    # Example usage (structured output with score + reasoning)
    structured_prompt = [
        {"role": "system", "content": "You evaluate relevance. Respond ONLY with a score (integer) and reasoning (text)."},
        {"role": "user", "content": (
            "Give a point about its relevance to the Israel-Palestine conflict. "
            "1 to 10. 1 being irrelevant 10 being very much relevant.\n\n"
            "TEXT:\nABD Başkanı Trump, İsrail'in ateşkesi ihlal ederek Gazze'ye düzenlediği saldırıların Gazze'deki ateşkesi tehlikeye atmayacağını ifade etti. Söz konusu ateşkesi 'çok büyük bir barış' olarak niteleyen Trump, Hamas'ın silah bırakmaya başladığını çünkü ateşkesin ikinci aşamasına girildiğini söyledi"
        )},
    ]

    print("\nCalling openai/gpt-5-mini (structured output)...")
    structured = await chat_completion_async(chat_history=structured_prompt, use_structured=True)
    # If structured is a Pydantic model (Evaluation), you can access fields like this:
    try:
        print("\nResponse (structured Evaluation):")
        print("score:", structured.score)
        print("reasoning:", structured.reasoning)
    except AttributeError:
        # If your structured client returns a dict-like object
        print("\nResponse (structured Evaluation):", structured)

    # # Non-structured example:
    # plain_prompt = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Say hello briefly."},
    # ]
    # print("\nCalling openai/gpt-5-mini (plain text)...")
    # text = await chat_completion_async(chat_history=plain_prompt, use_structured=False)
    # print("\nResponse (text):", text)

if __name__ == "__main__":
    asyncio.run(main())
