import os
import feedparser
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup

# ========== ニュース取得 ==========
WEB3_RSS = "https://www.blockchaingamer.biz/feed/"
AI_RSS = "https://venturebeat.com/category/ai/feed/"

def fetch_latest_article(rss_url):
    feed = feedparser.parse(rss_url)
    latest = feed.entries[0]
    return {
        "title": latest.title,
        "summary": latest.summary,
        "link": latest.link
    }

def clean_summary(html):
    return BeautifulSoup(html, "html.parser").get_text()

web3_article = fetch_latest_article(WEB3_RSS)
ai_article = fetch_latest_article(AI_RSS)

web3_article["summary"] = clean_summary(web3_article["summary"])
ai_article["summary"] = clean_summary(ai_article["summary"])

# ========== Hugging Face 記事生成 ==========
HF_API_URL = "https://api-inference.huggingface.co/models/rinna/japanese-gpt2-medium"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def generate_article(content):
    prompt = f"""
この文章は日本語です。次の内容について日本語で500-800字の記事を作成してください。
・要約（翻訳含む）
・私見を300字程度
・出典リンクを最後に記載

タイトル: {content["title"]}
要約元: {content["summary"]}
出典: {content["link"]}
"""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    res = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=60)

    print(f"HF API status: {res.status_code}")
    print(f"HF API response: {res.text[:500]}")

    if res.status_code != 200:
        raise Exception(f"Hugging Face API failed with status {res.status_code}: {res.text}")

    result = res.json()
    if 'error' in result:
        raise Exception(f"Hugging Face API error: {result['error']}")

    return result[0]['generated_text'] if isinstance(result, list) else result['generated_text']

web3_text = generate_article(web3_article)
ai_text = generate_article(ai_article)

# ========== Stable Horde 画像生成 ==========
HORDE_API_URL = "https://stablehorde.net/api/v2/generate/async"
HORDE_API_KEY = os.getenv("HORDE_API_KEY")

def generate_image(prompt, filename):
    payload = {
        "prompt": prompt,
        "params": {
            "n": 1,
            "width": 512,
            "height": 512
        }
    }
    headers = {"apikey": HORDE_API_KEY, "Content-Type": "application/json"}
    res = requests.post(HORDE_API_URL, headers=headers, json=payload)

    if res.status_code not in [200, 202]:
        raise Exception(f"Stable Horde API failed with status {res.status_code}: {res.text}")

    job = res.json()
    if 'id' not in job:
        raise Exception("Stable Horde API failed to start job")

    job_id = job['id']
    print(f"画像生成ジョブID: {job_id}")

    # ポーリングで画像ができるのを待つ
    fetch_url = f"https://stablehorde.net/api/v2/generate/status/{job_id}"
    while True:
        time.sleep(5)
        status_res = requests.get(fetch_url, headers={"apikey": HORDE_API_KEY})
        status = status_res.json()
        if status.get("done"):
            break
        print("画像生成中...")

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

today = datetime.now().strftime("%Y%m%d")
web3_img = generate_image(web3_article["title"], today + "_web3")
ai_img = generate_image(ai_article["title"], today + "_ai")

# ========== Markdown保存 ==========
def save_markdown(filename, title, content, image_path):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
---

# {title}

![記事画像]({image_path})

{content}
""")

save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-web3.md", web3_article["title"], web3_text, web3_img)
save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-ai.md", ai_article["title"], ai_text, ai_img)
