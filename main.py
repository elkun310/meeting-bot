from fastapi import FastAPI, Request
import subprocess
import requests
import os
import json
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import time
import locale
from langdetect import detect, DetectorFactory
from datetime import datetime

DetectorFactory.seed = 0
app = FastAPI()

# Load environment variables
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OLLAMA_MODEL = "llama3"
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Cache cho tenant access token
tenant_token_cache = {"token": None, "expire_time": 0}

def get_tenant_access_token():
    """Lấy tenant access token từ Lark"""
    if tenant_token_cache["token"] and time.time() < tenant_token_cache["expire_time"]:
        return tenant_token_cache["token"]
    
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        token = result["tenant_access_token"]
        tenant_token_cache["token"] = token
        tenant_token_cache["expire_time"] = time.time() + result.get("expire", 7200) - 300
        return token
    else:
        raise Exception(f"Failed to get tenant token: {result}")

# Deduplicate cache theo message_id
processed_messages = set()  # lưu tuple (message_id, chat_id)

@app.post("/webhook")
async def receive_meeting(request: Request):
    body = await request.json()

    # ✅ Xử lý challenge từ Lark
    if "challenge" in body:
        return JSONResponse(content={"challenge": body["challenge"]})

    event = body.get("event", {})
    message = event.get("message", {})
    chat_id = message.get("chat_id")
    message_id = message.get("message_id")
    message_type = message.get("message_type")

    # Deduplicate theo message_id + chat_id
    key = (message_id, chat_id)
    if key in processed_messages:
        print(f"⚠️ Duplicate message {key}, ignoring...")
        return {"status": "duplicate"}
    processed_messages.add(key)

    # Chỉ xử lý text message
    if message_type != "text":
        return {"status": "ignored", "reason": "not a text message"}

    content = message.get("content", "{}")
    try:
        text = json.loads(content).get("text", "")
    except json.JSONDecodeError:
        text = content

    if not text or not text.strip():
        return {"status": "ignored", "reason": "empty text"}

    # Tránh loop từ bot
    sender = event.get("sender", {})
    if sender.get("sender_type") == "app":
        return {"status": "ignored", "reason": "message from bot"}

    print(f"✅ Processing message: {text[:100]}...")

    try:
        # Tóm tắt
        print("🤖 Summarizing with Ollama...")
        summary = summarize_with_groq(text)
        print(f"✅ Summary generated: {summary[:100]}...")

        # Lưu vào Notion
        print("💾 Saving to Notion...")
        notion_response = save_to_notion(text, summary)
        print(f"✅ Notion response: {notion_response.status_code}")

        # Gửi kết quả về Lark
        print("📤 Sending message to Lark...")
        send_message_to_lark(summary, chat_id)
        print("✅ Message sent!")

        return {"status": "success", "summary": summary, "notion_status": notion_response.status_code}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

def summarize_with_groq(text):
    """Tóm tắt văn bản bằng Groq API, tự động theo ngôn ngữ văn bản"""
    
    # Detect ngôn ngữ
    # try:
    #     lang = detect(text)
    # except:
    #     lang = "en"
    
    # Tùy theo ngôn ngữ, tạo prompt
    # if lang == "vi":
    prompt = f"Tóm tắt ngắn gọn nội dung cuộc họp sau bằng tiếng Việt, nêu các điểm chính:\n\n{text}"
    # elif lang == "ja":
    #     prompt = f"以下の会議内容を簡潔に日本語でまとめ、重要なポイントを箇条書きしてください：\n\n{text}"
    # else:
    #     prompt = f"Summarize the following meeting notes in English, highlighting the key points:\n\n{text}"
    
    if not GROQ_API_KEY:
        return "❌ Thiếu GROQ_API_KEY trong file .env. Đăng ký tại https://console.groq.com/"

    try:
        response = requests.post(
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

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"❌ Lỗi Groq API ({response.status_code}): {response.text}"
    except requests.exceptions.Timeout:
        return "⏱️ Groq API timeout"
    except Exception as e:
        return f"❌ Lỗi Groq: {str(e)}"
    
def save_to_notion(original_text, summary):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    def truncate_text(text, max_length=1900):
        return text[:max_length] + "..." if len(text) > max_length else text

    # Detect ngôn ngữ
    try:
        lang = detect(original_text)
    except:
        lang = "en"  # fallback nếu detect fail

    # Set locale, format ngày và tiêu đề theo ngôn ngữ
    if lang == "vi":
        try:
            locale.setlocale(locale.LC_TIME, "vi_VN.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "")
        date_str = datetime.now().strftime("%d/%m/%Y")
        title = f"Tóm tắt cuộc họp - {date_str}"
        
    elif lang == "ja":
        now = datetime.now()
        date_str = f"{now.year}年{now.month}月{now.day}日"
        title = f"会議の要約 - {date_str}"
        
    elif lang == "ko":
        now = datetime.now()
        date_str = f"{now.year}년 {now.month}월 {now.day}일"
        title = f"회의 요약 - {date_str}"
        
    elif lang == "zh-cn" or lang == "zh-tw":
        now = datetime.now()
        date_str = f"{now.year}年{now.month}月{now.day}日"
        title = f"会议总结 - {date_str}"
        
    else:  # English và các ngôn ngữ khác
        try:
            locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "")
        date_str = datetime.now().strftime("%b %d, %Y")
        title = f"Meeting Summary - {date_str}"

    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Meeting Title": {"title": [{"text": {"content": title}}]},
            "Full Transcript": {"rich_text": [{"text": {"content": truncate_text(original_text)}}]},
            "Summary": {"rich_text": [{"text": {"content": truncate_text(summary)}}]}
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response

def send_message_to_lark(summary, chat_id):
    token = get_tenant_access_token()
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    params = {"receive_id_type": "chat_id"}
    data = {"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": f"📝 Tóm tắt cuộc họp:\n\n{summary}"})}
    response = requests.post(url, headers=headers, params=params, json=data)
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
