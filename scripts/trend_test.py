"""流行事象キャッチアップ - Slack投稿テスト版"""
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import os
import re
import random
from datetime import datetime

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

BOOST_KEYWORDS = [
    "ai", "新サービス", "新商品", "launch", "startup",
    "d2c", "サブスク", "web3", "xr", "ウェルネス",
    "サステナブル", "コミュニティ", "クリエイター",
    "z世代", "gen z", "tiktok", "viral",
]
BOOST_SOURCES = ["product hunt", "lobsterr"]
MAX_ARTICLES = 5  # 厳選5件

RSS_FEEDS = [
    # --- プロダクト / サービス ---
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed", "category": "プロダクト / サービス"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "プロダクト / サービス"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "プロダクト / サービス"},
    {"name": "Yanko Design", "url": "https://www.yankodesign.com/feed/", "category": "プロダクト / サービス"},
    {"name": "IDEAS FOR GOOD", "url": "https://ideasforgood.jp/feed/", "category": "プロダクト / サービス"},
    # --- カルチャー / ライフスタイル ---
    {"name": "TABI LABO", "url": "https://tabi-labo.com/feed", "category": "カルチャー / ライフスタイル"},
    {"name": "Hypebeast", "url": "https://hypebeast.com/feed", "category": "カルチャー / ライフスタイル"},
    {"name": "designboom", "url": "https://www.designboom.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "Cool Hunting", "url": "https://coolhunting.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "CINRA", "url": "https://www.cinra.net/feed", "category": "カルチャー / ライフスタイル"},
    # --- lobsterr / 社会変化 / 傍流カルチャー ---
    {"name": "Lobsterr FM", "url": "https://anchor.fm/s/da77454/podcast/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Monocle", "url": "https://monocle.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "NOWNESS", "url": "https://www.nowness.com/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Colossal", "url": "https://www.thisiscolossal.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "Creative Boom", "url": "https://www.creativeboom.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "The Guardian - Culture", "url": "https://www.theguardian.com/culture/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Aeon", "url": "https://aeon.co/feed.rss", "category": "カルチャー / ライフスタイル"},
    # --- テック / イノベーション ---
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "category": "テック / イノベーション"},
    {"name": "Trend Hunter", "url": "https://www.trendhunter.com/rss", "category": "テック / イノベーション"},
    {"name": "AXIS", "url": "https://www.axismag.jp/feed", "category": "テック / イノベーション"},
]

seen_titles = set()
seen_links = set()


def fetch_rss(feed):
    articles = []
    try:
        req = urllib.request.Request(
            feed["url"],
            headers={"User-Agent": "Trend-Morning-News-Bot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()

        root = ET.fromstring(data)

        # RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            if not title or not link:
                continue
            if title in seen_titles or link in seen_links:
                continue
            seen_titles.add(title)
            seen_links.add(link)
            articles.append({
                "title": title, "link": link,
                "source": feed["name"], "category": feed["category"],
            })

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            if title_el is None or link_el is None:
                continue
            title = title_el.text.strip() if title_el.text else ""
            link = link_el.get("href", "").strip()
            if not title or not link:
                continue
            if title in seen_titles or link in seen_links:
                continue
            seen_titles.add(title)
            seen_links.add(link)
            articles.append({
                "title": title, "link": link,
                "source": feed["name"], "category": feed["category"],
            })

    except Exception as e:
        print(f"[WARN] {feed['name']} の取得に失敗: {e}")

    return articles[:5]


def score_article(article):
    s = 0
    title_lower = article["title"].lower()
    source_lower = article["source"].lower()
    for kw in BOOST_KEYWORDS:
        if kw in title_lower:
            s += 2
    for src in BOOST_SOURCES:
        if src in source_lower:
            s += 3
    return s


def post_to_slack(message):
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        return response.read()


def main():
    today = datetime.now().strftime("%Y/%m/%d")
    print("=== 流行事象キャッチアップ Bot テスト ===")

    all_articles = []
    for feed in RSS_FEEDS:
        print(f"  取得中: {feed['name']}")
        articles = fetch_rss(feed)
        all_articles.extend(articles)
        print(f"    → {len(articles)}件")

    print(f"\n合計取得: {len(all_articles)}件")

    if not all_articles:
        post_to_slack(f":earth_americas: *culturai朝刊 - {today}*\n\n本日の新着トレンドはありませんでした。")
        return

    # スコアリング
    for a in all_articles:
        a["score"] = score_article(a)

    random.shuffle(all_articles)
    all_articles.sort(key=lambda a: a["score"], reverse=True)

    # 同一ソース最大1件（5件に厳選するため偏り防止）
    source_count = {}
    picked = []
    for a in all_articles:
        count = source_count.get(a["source"], 0)
        if count < 1:
            source_count[a["source"]] = count + 1
            picked.append(a)
        if len(picked) >= MAX_ARTICLES:
            break

    # Slackメッセージ構築
    lines = [f":earth_americas: *culturai朝刊 - {today}*\n"]
    lines.append("今日の注目トレンド :sparkles:\n")

    for i, a in enumerate(picked, 1):
        lines.append(f"*{i}.* <{a['link']}|{a['title']}>")
        lines.append(f"    _{a['source']}_\n")

    lines.append("今日も良い一日を :coffee:")

    print(f"投稿件数: {len(picked)}件")

    message = "\n".join(lines)
    post_to_slack(message)
    print("Slack に投稿しました!")


if __name__ == "__main__":
    main()
