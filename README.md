# 🤖 AI Meeting Summary Bot for Lark & Slack

An automated bot that summarizes meeting conversations in Lark (Feishu) and Slack using AI and stores them in Notion.

## ✨ Features

- 📝 **Auto Summarization**: Receives messages from Lark/Slack and summarizes using AI (Groq)
- 🤖 **Smart Triggers**: Bot activates only when @mentioned or with keywords (`/summary`, `/tóm tắt`)
- 🌍 **Multi-language**: Supports Vietnamese, Japanese, English, Korean, Chinese
- 💾 **Notion Storage**: Automatically saves original content and summaries to Notion database
- 🔄 **Real-time**: Processes messages instantly via webhook
- 🚫 **Duplicate Prevention**: Avoids processing duplicate messages
- 🔌 **Multi-platform**: Works with both Lark and Slack simultaneously

## 🛠️ Tech Stack

- **FastAPI**: Web framework for webhook server
- **Groq API**: AI model for summarization (llama-3.1-8b-instant)
- **Notion API**: Data storage
- **Lark API**: Message receiving and sending
- **Slack API**: Message receiving and sending
- **langdetect**: Automatic language detection

## 📋 Requirements

- Python 3.8+
- Lark Developer account (optional)
- Slack workspace with admin access (optional)
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

# Groq API Configuration
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Lark Configuration (optional - leave empty if not using)
LARK_APP_ID=cli_xxxxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Slack Configuration (optional - leave empty if not using)
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
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

### C. Slack Setup

1. **Create App:**

   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "Meeting Summary Bot"
   - Select your workspace

2. **Configure Bot Token:**

   - Go to "OAuth & Permissions"
   - Add Bot Token Scopes:
     - `channels:history` (Read public channels)
     - `groups:history` (Read private channels)
     - `chat:write` (Send messages)
   - Click "Install to Workspace"
   - Copy **Bot User OAuth Token** → `SLACK_BOT_TOKEN`

3. **Setup Event Subscriptions:**

   - Go to "Event Subscriptions"
   - Enable Events: ON
   - Request URL: `https://your-domain.com/slack/events`
   - Subscribe to bot events:
     - `message.channels`
     - `message.groups`
   - Save Changes

4. **Add Bot to Channel:**
   - Open Slack channel
   - Type: `/invite @Meeting Summary Bot`

### D. Groq Setup

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

Copy ngrok URL and update in:

- Lark Event Subscriptions: `https://xxx.ngrok.io/webhook`
- Slack Event Subscriptions: `https://xxx.ngrok.io/slack/events`

### Production

Deploy to:

- **Railway**: https://railway.app
- **Render**: https://render.com
- **Heroku**: https://heroku.com
- **VPS**: DigitalOcean, AWS EC2, etc.

## 📝 Usage

### Triggering the Bot

The bot will ONLY respond when:

**Option 1: @mention the bot**

```
@Meeting Summary Bot
Today's meeting discussed:
- Product launch on Dec 20
- Marketing team to prepare content
```

**Option 2: Use keyword trigger**

```
/summary
Meeting notes:
- Product launch on Dec 20
- Marketing prep content
```

Supported keywords: `/summary`, `/tóm tắt`, `/tomtat`, `!summary`

### Bot Workflow

When triggered, bot will:

1. ✅ Detect language automatically
2. ✅ Summarize content with AI
3. ✅ Save to Notion (with platform tag)
4. ✅ Send summary back to group/channel

### Example

**Input (Lark/Slack):**

```
User: @Meeting Summary Bot
Hôm nay team họp về:
- Launch sản phẩm ngày 20/12
- Team marketing chuẩn bị content
- John phụ trách thiết kế
```

**Output:**

```
Bot: 📝 Tóm tắt cuộc họp:

Cuộc họp tập trung vào kế hoạch ra mắt sản phẩm vào ngày 20/12.
Các điểm chính:
- Team marketing sẽ chuẩn bị nội dung
- John đảm nhận phần thiết kế
```

**Notion Entry:**

- Title: `[Lark] Tóm tắt cuộc họp - 13/11/2025`
- Full Transcript: (original message)
- Summary: (AI summary)

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

Response:

```json
{
  "status": "healthy",
  "platforms": {
    "lark": true,
    "slack": true
  }
}
```

## 🌐 Platform Support

| Platform  | Webhook Endpoint | Trigger Methods    |
| --------- | ---------------- | ------------------ |
| **Lark**  | `/webhook`       | @mention, keywords |
| **Slack** | `/slack/events`  | @mention, keywords |

You can use:

- ✅ Only Lark (leave `SLACK_BOT_TOKEN` empty)
- ✅ Only Slack (leave `LARK_APP_ID` and `LARK_APP_SECRET` empty)
- ✅ Both platforms simultaneously

## 📄 License

MIT License

## 🤝 Contributing

Contributions, issues and feature requests are welcome!

---

⭐ If you find this project useful, please star the repo!
