import os
import feedparser
import requests
import re
from datetime import datetime
import time

# ========== テキスト後処理 ==========
def clean_generated_text(text):
    unwanted_phrases = [
        r"次の内容について日本語で.*?",
        r"要約（翻訳含む）",
        r"私見を.*?",
        r"出典リンクを.*?",
        r"500～800字",
        r"記事例.*?(参考：|$)",
        r"情報：.*?(参考：|$)"
    ]
    for phrase in unwanted_phrases:
        text = re.sub(phrase, "", text, flags=re.MULTILINE | re.DOTALL)
    if re.search(r"[a-zA-Z\s]{20,}", text):
        print("警告: 生成テキストに英語が含まれています")
    return text.strip()

# ========== ニュース取得 ==========
WEB3_RSS = "https://www.blockchaingamer.biz/feed/"
AI_RSS = "https://venturebeat.com/category/ai/feed/"

def fetch_latest_article(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            raise Exception(f"No entries found in RSS feed: {rss_url}")
        latest = feed.entries[0]
        return {
            "title": latest.title,
            "summary": latest.summary,
            "link": latest.link
        }
    except Exception as e:
        raise Exception(f"Failed to fetch RSS feed from {rss_url}: {str(e)}")

try:
    web3_article = fetch_latest_article(WEB3_RSS)
    ai_article = fetch_latest_article(AI_RSS)
except Exception as e:
    print(f"Error fetching articles: {str(e)}")
    raise

# ========== 記事テキスト読み込み（Colab生成済み） ==========
def read_article_file(filename, fallback_text="記事生成に失敗しました。後で再試行してください。"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return clean_generated_text(f.read())
    print(f"警告: {filename} が見つかりません。フォールバックテキストを使用。")
    return fallback_text

try:
    web3_text = read_article_file("web3_article.txt")
    ai_text = read_article_file("ai_article.txt")
except Exception as e:
    print(f"Error reading article files: {str(e)}")
    raise

# ========== Stable Horde 画像生成 ==========
HORDE_API_URL = "https://stablehorde.net/api/v2/generate/async"
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

if not HORDE_API_KEY:
    raise Exception("HORDE_API_KEY is empty or not set! Check your GitHub Secrets.")

def generate_image(prompt, filename):
    image_prompt = f"A vibrant digital illustration of {prompt} in a futuristic cyberpunk style"
    payload = {
        "prompt": image_prompt,
        "params": {
            "n": 1,
            "width": 512,
            "height": 512
        }
    }
    headers = {"apikey": HORDE_API_KEY, "Content-Type": "application/json"}
    try:
        res = requests.post(HORDE_API_URL, headers=headers, json=payload)
        if res.status_code not in [200, 202]:
            raise Exception(f"Stable Horde API failed with status {res.status_code}: {res.text}")
        job = res.json()
        if 'id' not in job:
            raise Exception("Stable Horde API failed to start job")
        job_id = job['id']
        print(f"画像生成ジョブID: {job_id}")
        fetch_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"
        max_attempts = 24  # 120秒待機
        for _ in range(max_attempts):
            time.sleep(5)
            status_res = requests.get(fetch_url, headers={"apikey": HORDE_API_KEY-controlled access to Grok, created by xAI.
