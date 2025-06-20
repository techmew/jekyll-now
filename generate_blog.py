import feedparser
import requests
from datetime import datetime
import json

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

web3_article = fetch_latest_article(WEB3_RSS)
ai_article = fetch_latest_article(AI_RSS)

# ========== Hugging Face 無料LLMで記事生成 ==========
# 例：Hugging Face API (Mistralモデルなど)
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def generate_article(content, category):
    prompt = f"""
次の内容について日本語で500-800字の記事を作成してください。
・要約（翻訳含む）
・私見を300字程度
・出典リンクを最後に記載

タイトル: {content["title"]}
要約元: {content["summary"]}
出典: {content["link"]}
"""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt})
    result = response.json()
    return result[0]['generated_text'] if isinstance(result, list) else result['generated_text']

web3_text = generate_article(web3_article, "web3")
ai_text = generate_article(ai_article, "ai")

# ========== Stable Hordeで画像生成 ==========
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
    job = res.json()
    # 通常ここで polling が必要（簡易例なのでここまで）
    print(f"画像生成ジョブID: {job.get('id')}")
    # ダウンロード処理は別途実装推奨
    return f"assets/images/{filename}.png"

web3_img = generate_image(web3_article["title"], datetime.now().strftime("%Y%m%d") + "_web3")
ai_img = generate_image(ai_article["title"], datetime.now().strftime("%Y%m%d") + "_ai")

# ========== Markdown保存 ==========
def save_markdown(filename, title, content, image_path):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""---
layout: post
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d')}
---

![記事画像]({image_path})

{content}
""")

save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-web3.md", web3_article["title"], web3_text, web3_img)
save_markdown(f"_posts/{datetime.now().strftime('%Y-%m-%d')}-ai.md", ai_article["title"], ai_text, ai_img)
