# 🤖 AI Meeting Summary Bot for Lark

An automated bot that summarizes meeting conversations in Lark (Feishu) using AI and stores them in Notion.

## ✨ Features

- 📝 **Auto Summarization**: Receives messages from Lark groups and summarizes using AI (Groq)
- 🌍 **Multi-language**: Supports Vietnamese, Japanese, English, Korean, Chinese
- 💾 **Notion Storage**: Automatically saves original content and summaries to Notion database
- 🔄 **Real-time**: Processes messages instantly via webhook
- 🚫 **Duplicate Prevention**: Avoids processing duplicate messages

## 🛠️ Tech Stack

- **FastAPI**: Web framework for webhook server
- **Groq API**: AI model for summarization (llama-3.1-8b-instant)
- **Notion API**: Data storage
- **Lark API**: Message receiving and sending
- **langdetect**: Automatic language detection

## 📋 Requirements

- Python 3.8+
- Lark Developer account
- Notion account
- Groq account (free)
- Ngrok (for development) or public server

## 🚀 Installation

### 1. Clone repository

```bash
git clone <repository-url>
cd meeting-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi
uvicorn
requests
python-dotenv
pydantic
langdetect
```

### 3. Environment configuration

Create `.env` file:

```env
# Notion Configuration
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Lark Configuration
LARK_APP_ID=cli_xxxxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Groq API Configuration
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 🔧 Setup Guide

### A. Notion Setup

1. **Create Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Name it: "Meeting Summary Bot"
   - Copy **Internal Integration Secret** → `NOTION_API_KEY`

2. **Create Database:**
   - Create new page in Notion
   - Add Table with 3 columns:
     - `Meeting Title` (Title)
     - `Full Transcript` (Text)
     - `Summary` (Text)

3. **Connect Integration:**
   - Open database → Click "..." → "Connections"
   - Select "Meeting Summary Bot"
   - Confirm

4. **Get Database ID:**
   - Copy database URL
   - Extract 32-character string: `https://notion.so/xxxxxxxx...`

### B. Lark Setup

1. **Create App:**
   - Go to https://open.larksuite.com/app
   - Click "Create custom app"

2. **Get Credentials:**
   - Go to "Credentials & Basic Info"
   - Copy **App ID** → `LARK_APP_ID`
   - Copy **App Secret** → `LARK_APP_SECRET`

3. **Configure Permissions:**
   - Go to "Permissions & Scopes"
   - Add:
     - `im:message` (Receive messages)
     - `im:message:send_as_bot` (Send messages)
     - `im:chat` (Access chat info)

4. **Setup Webhook:**
   - Go to "Event Subscriptions"
   - Request URL: `https://your-domain.com/webhook`
   - Subscribe to event: `im.message.receive_v1`
   - Save

5. **Publish App:**
   - Go to "Version Management & Release"
   - Create version → Publish

6. **Add Bot to Group:**
   - Open group chat in Lark
   - Click group name → "Bots" → "Add Bot"
   - Select your bot

### C. Groq Setup

1. Go to https://console.groq.com/
2. Sign up (free)
3. Go to "API Keys" → "Create API Key"
4. Copy key → `GROQ_API_KEY`

## 🏃 Running the Bot

### Development (Local)

**Terminal 1: Run FastAPI**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Run ngrok**
```bash
ngrok http 8000
```

Copy ngrok URL and update in Lark Event Subscriptions.

### Production

Deploy to:
- **Railway**: https://railway.app
- **Render**: https://render.com
- **Heroku**: https://heroku.com
- **VPS**: DigitalOcean, AWS EC2, etc.

## 📝 Usage

1. Add bot to Lark group
2. Send any message to the group
3. Bot will:
   - ✅ Detect language
   - ✅ Summarize content
   - ✅ Save to Notion
   - ✅ Send summary back to group

**Example:**

```
User: Today's meeting discussed:
- Product launch on Dec 20
- Marketing team to prepare content
- John handles design

Bot: 📝 Meeting Summary:
The meeting focused on product launch planning...
```

## 🧪 Testing

### Test Notion API
```bash
python test_notion.py
```

### Test Groq API
```bash
python test_groq.py
```

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions, issues and feature requests are welcome!

---

⭐ If you find this project useful, please star the repo!