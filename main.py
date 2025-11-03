import os
import asyncio
import aiohttp
from datetime import datetime, timezone
from dotenv import load_dotenv
import traceback  # Import traceback to get detailed error information

from config.feeds_config import FEEDS
from core.helpers import load_last_run_time, save_last_run_time, extract_score_reason
from core.rss_fetcher import fetch_feed_content
from core.relevance_analyzer import analyze_relevance_async
from core.send_email import send_email

LLM_CONCURRENCY = 32

async def process_feed(feed, session, sem, email_cfg):
    """
    Process a single feed, sending an email on failure and always updating the timestamp.
    """
    name = feed["name"]
    start_time = datetime.now(timezone.utc)  # Consistent timestamp for this run

    try:
        urls = feed["urls"]
        postprocess_fn = feed["postprocess_fn"]

        print(f"\n📡 Processing feed: {name}")

        last_run = load_last_run_time(name)
        if last_run:
            print(f"Last run for {name}: {last_run.strftime('%a, %d %b %Y %H:%M:%S GMT')}")
        else:
            print(f"First run for {name} (no previous timestamp found)")

        # --- Fetch raw feed content ---
        fetch_tasks = [fetch_feed_content(session, url) for url in urls]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        # print(results)
        # raise Exception("Debug Exception: Inspect fetched results")  # Debugging line

        # --- Postprocess: parse and standardize feed content ---
        processed_items = []
        for res in results:
            if isinstance(res, Exception):
                print(f"❌ Fetch error in {name}: {res}")
                continue
            try:
                items = postprocess_fn(res)  # feed-specific parser
                processed_items.extend(items)
            except Exception as e:
                print(f"❌ Postprocessing error for {name}: {e}")

        # --- Filter new items ---
        new_items = [
            it for it in processed_items
            if it["pub_date"] is not None
            and (last_run is None or it["pub_date"] > last_run)
        ]
        new_items.sort(key=lambda x: x["pub_date"], reverse=True)

        if not new_items:
            print(f"No new items in {name}.")
            return

        print(f"🆕 {len(new_items)} new items from {name}")

        # --- Analyze relevance (feed-specific prompt) ---
        base_prompt = feed.get("llm_prompt")

        llm_tasks = [
            analyze_relevance_async(it["description"], sem, base_prompt)
            for it in new_items
        ]
        llm_results = await asyncio.gather(*llm_tasks, return_exceptions=True)

        relevant_items_for_email = []
        for item, result in zip(new_items, llm_results):
            if isinstance(result, Exception):
                print(f"Error analyzing {item['title']}: {result}")
                continue

            score, reason = extract_score_reason(result)
            #print(score, reason)
            if score and score > 5:
                print(f"✅ Relevant: {item['title']} ({score})")
                relevant_items_for_email.append((item, score, reason))

        # --- Send email for relevant items ---
        if relevant_items_for_email:
            body_lines = [f"Found {len(relevant_items_for_email)} relevant articles in {name}:\n"]
            for item, score, reason in relevant_items_for_email:
                body_lines.append("---")
                body_lines.append(f"Title: {item['title']}")
                body_lines.append(f"Link: {item['link']}")
                body_lines.append(f"Relevance Score: {score}")
                body_lines.append(f"Reasoning: {reason}\n")

            try:
                send_email(
                    subject=f"AI News Alert: {name}",
                    body="\n".join(body_lines),
                    **email_cfg,
                )
            except Exception as e:
                print(f"❌ Email failed for {name}: {e}")

    except Exception as e:
        # If any part of the process fails, log it and send an email alert.
        print(f"❌ CRITICAL ERROR processing feed '{name}': {e}")
        error_details = traceback.format_exc()
        print(error_details)
        try:
            send_email(
                subject=f"CRITICAL ERROR in News Reporter: Failed to process '{name}'",
                body=f"The news reporter failed to process the '{name}' feed.\n\nError:\n{error_details}",
                **email_cfg,
            )
        except Exception as mail_e:
            print(f"❌ Additionally, failed to send error email: {mail_e}")

    finally:
        # --- Always save the last run time to prevent reprocessing a failing feed ---
        save_last_run_time(name, start_time)
        print(f"✅ Updated last run time for {name} to {start_time.strftime('%a, %d %b %Y %H:%M:%S GMT')}\n")


async def main():
    load_dotenv()

    email_cfg = {
        "to_emails": [e.strip() for e in os.getenv("TO_EMAILS", "").split(",") if e.strip()],
        "email_user": os.getenv("EMAIL_USER"),
        "email_pass": os.getenv("EMAIL_PASS"),
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
    }

    sem = asyncio.Semaphore(LLM_CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        for feed in FEEDS:
            await process_feed(feed, session, sem, email_cfg)


# Use this for local use
if __name__ == "__main__":
   asyncio.run(main())

# # Use this (uncomment) for AWS Lambda
# def lambda_handler(event, context):
#     asyncio.run(main())
