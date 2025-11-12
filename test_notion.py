import requests
import os
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Xóa dấu gạch ngang nếu có
NOTION_DATABASE_ID = NOTION_DATABASE_ID.replace("-", "")

print(f"Testing with:")
print(f"Token starts with: {NOTION_API_KEY[:7]}...")
print(f"Database ID: {NOTION_DATABASE_ID}")
print()

# Test query database
url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json={})
print(f"Status: {response.status_code}")
print(response.json())