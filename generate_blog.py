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

# ========== 記事テキストはColabで生成済みと仮定 ==========
# 例: _gorok.pyで生成したテキストを読み込む
try:
    with open("web3_article.txt", "r", encoding="utf-8") as f:
        web3_text = clean_generated_text(f.read())
    with open("ai_article.txt", "r", encoding="utf-8") as f:
        ai_text = clean_generated_text(f.read())
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
            status_res = requests.get(fetch_url, headers={"apikey": HORDE_API_KEY})
            status = status_res.json()
            if status.get("done"):
                break
            print("画像生成中...")
        else:
            raise Exception("画像生成がタイムアウトしました")
        if not status.get("generations"):
            raise Exception("画像生成に失敗しました")
        img_url = status["generations"][0]["img"]
        img_data = requests.get(img_url).content
        img_path = f"assets/images/{filename}.png"
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(img_data)
        print(f"画像保存済み: {img_path}")
        return img_path
    except Exception as e:
        raise Exception(f"Failed to generate image: {str(e)}")

try:
    today = datetime.now().strftime("%Y%m%d")
    web3_img = generate_image(web3_article["title"], today + "_web3")
    ai_img = generate_image(ai_article["title"], today + "_ai")
except Exception as e:
    print(f"Error generating images: {str(e)}")
    raise

# ========== Markdown保存 ==========
def save_markdown(filename, title, content, image_path):
    try:
        escaped_title = title.replace('"', '\\"')
        markdown_content = f"""---
layout: post
title: "{escaped_title}"
date: {datetime.now().strftime('%Y-%m-%d')}
---

![記事画像]({image_path})

{content}
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Markdown保存済み: {filename}")
    except Exception as e:
        raise Exception(f"Failed to save markdown: {str(e)}")

try:
    save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-web3.md", web3_article["title"], web3_text, web3_img)
    save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-ai.md", ai_article["title"], ai_text, ai_img)
except Exception as e:
    print(f"Error saving markdown: {str(e)}")
    raise
