from fastapi import FastAPI, Request
import requests
import os
import json
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import time
from langdetect import detect, DetectorFactory
from datetime import datetime

DetectorFactory.seed = 0
app = FastAPI()

# Load environment variables
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Lark credentials
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")

# Slack credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Cache & dedup
tenant_token_cache = {"token": None, "expire_time": 0}
processed_messages = set()

# ==================== LARK TOKEN ====================
def get_tenant_access_token():
    if tenant_token_cache["token"] and time.time() < tenant_token_cache["expire_time"]:
        return tenant_token_cache["token"]

    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    res = requests.post(url, headers=headers, json=data).json()

    if res.get("code") == 0:
        token = res["tenant_access_token"]
        tenant_token_cache["token"] = token
        tenant_token_cache["expire_time"] = time.time() + res.get("expire", 7200) - 300
        return token
    raise Exception("Failed to get Lark tenant token")

# ==================== LARK WEBHOOK ====================
@app.post("/webhook")
async def lark_webhook(request: Request):
    body = await request.json()

    if "challenge" in body:
        return JSONResponse(content={"challenge": body["challenge"]})

    event = body.get("event", {})
    message = event.get("message", {})
    chat_id = message.get("chat_id")
    message_id = message.get("message_id")
    message_type = message.get("message_type")

    if (message_id, chat_id, "lark") in processed_messages:
        return {"status": "duplicate"}
    processed_messages.add((message_id, chat_id, "lark"))

    if message_type != "text":
        return {"status": "ignored"}

    try:
        text = json.loads(message.get("content", "{}")).get("text", "")
    except json.JSONDecodeError:
        text = message.get("content", "")

    if not text.strip():
        return {"status": "ignored"}

    if event.get("sender", {}).get("sender_type") == "app":
        return {"status": "ignored"}

    # Trigger keywords
    trigger_keywords = ["/summary", "/tóm tắt", "/tomtat", "!summary", "!tóm tắt"]
    triggered = any(text.lower().strip().startswith(k) for k in trigger_keywords)
    if not triggered:
        return {"status": "ignored"}

    text = text.split(maxsplit=1)[-1] if " " in text else ""

    try:
        summary = summarize_with_groq(text)
        save_to_notion(text, summary, platform="Lark")
        send_message_to_lark(summary, chat_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==================== SLACK WEBHOOK ====================
@app.post("/slack/events")
async def slack_webhook(request: Request):
    body = await request.json()

    if body.get("type") == "url_verification":
        return JSONResponse(content={"challenge": body["challenge"]})

    if body.get("type") != "event_callback":
        return {"status": "ignored"}

    event = body.get("event", {})
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return {"status": "ignored"}

    if event.get("type") != "message":
        return {"status": "ignored"}

    text = event.get("text", "")
    channel = event.get("channel")
    ts = event.get("ts")

    if (ts, channel, "slack") in processed_messages:
        return {"status": "duplicate"}
    processed_messages.add((ts, channel, "slack"))

    if not text.strip():
        return {"status": "ignored"}

    # Trigger check
    import re
    text = re.sub(r"<@U[A-Z0-9]+>", "", text).strip()
    trigger_keywords = ["!summary", "!tóm tắt", "!tomtat", "summary:", "tóm tắt:"]
    triggered = any(text.lower().startswith(k) for k in trigger_keywords)
    if not triggered:
        return {"status": "ignored"}

    text = text.split(maxsplit=1)[-1] if " " in text else ""

    try:
        summary = summarize_with_groq(text)
        save_to_notion(text, summary, platform="Slack")
        send_message_to_slack(summary, channel)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==================== SHARED FUNCTIONS ====================
def summarize_with_groq(text):
    if not GROQ_API_KEY:
        return "❌ Missing GROQ_API_KEY"

    try:
        lang = detect(text)
    except:
        lang = "vi"

    if lang == "vi":
        prompt = f"Tóm tắt ngắn gọn nội dung cuộc họp sau bằng tiếng Việt:\n\n{text}"
    elif lang == "ja":
        prompt = f"以下の会議内容を日本語で簡潔にまとめてください:\n\n{text}"
    else:
        prompt = f"Summarize the following meeting notes in English:\n\n{text}"

    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        },
        timeout=30
    )

    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"].strip()
    return f"Groq API error: {res.status_code}"

def save_to_notion(original_text, summary, platform="Unknown"):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    def truncate(text, max_len=1900):
        return text[:max_len] + "..." if len(text) > max_len else text

    try:
        lang = detect(original_text)
    except:
        lang = "vi"

    now = datetime.now()
    if lang == "vi":
        title = f"[{platform}] Tóm tắt cuộc họp - {now:%d/%m/%Y}"
    elif lang == "ja":
        title = f"[{platform}] 会議の要約 - {now:%Y年%m月%d日}"
    else:
        title = f"[{platform}] Meeting Summary - {now:%b %d, %Y}"

    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Meeting Title": {"title": [{"text": {"content": title}}]},
            "Full Transcript": {"rich_text": [{"text": {"content": truncate(original_text)}}]},
            "Summary": {"rich_text": [{"text": {"content": truncate(summary)}}]}
        }
    }
    return requests.post(url, headers=headers, json=data)

def send_message_to_lark(summary, chat_id):
    token = get_tenant_access_token()
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    params = {"receive_id_type": "chat_id"}
    data = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": f"📝 Tóm tắt cuộc họp:\n\n{summary}"})
    }
    return requests.post(url, headers=headers, params=params, json=data)

def send_message_to_slack(summary, channel):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"channel": channel, "text": f"📝 *Meeting Summary:*\n\n{summary}"}
    requests.post(url, headers=headers, json=data)

# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "platforms": {
            "lark": bool(LARK_APP_ID and LARK_APP_SECRET),
            "slack": bool(SLACK_BOT_TOKEN)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
