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

# 設定
BOOST_KEYWORDS = [
    "ai", "新サービス", "新商品", "launch", "startup",
    "d2c", "サブスク", "web3", "xr", "ウェルネス",
    "サステナブル", "コミュニティ", "クリエイター",
    "z世代", "gen z", "tiktok", "viral",
]
BOOST_SOURCES = ["product hunt", "lobsterr"]
MAX_ARTICLES = 24

RSS_FEEDS = [
    # --- プロダクト / サービス ---
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed", "category": "プロダクト / サービス"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "プロダクト / サービス"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "プロダクト / サービス"},
    {"name": "Springwise", "url": "https://www.springwise.com/feed/", "category": "プロダクト / サービス"},
    {"name": "BRIDGE", "url": "https://thebridge.jp/feed", "category": "プロダクト / サービス"},
    # --- カルチャー / ライフスタイル ---
    {"name": "WIRED Japan", "url": "https://wired.jp/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "TABI LABO", "url": "https://tabi-labo.com/feed", "category": "カルチャー / ライフスタイル"},
    {"name": "Dezeen", "url": "https://www.dezeen.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "Hypebeast", "url": "https://hypebeast.com/feed", "category": "カルチャー / ライフスタイル"},
    {"name": "designboom", "url": "https://www.designboom.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "Cool Hunting", "url": "https://coolhunting.com/feed/", "category": "カルチャー / ライフスタイル"},
    # --- lobsterr / 社会変化 / 傍流カルチャー ---
    {"name": "Lobsterr FM", "url": "https://anchor.fm/s/da77454/podcast/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Monocle", "url": "https://monocle.com/feed/", "category": "カルチャー / ライフスタイル"},
    {"name": "It's Nice That", "url": "https://www.itsnicethat.com/rss/all", "category": "カルチャー / ライフスタイル"},
    {"name": "NOWNESS", "url": "https://www.nowness.com/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Wallpaper*", "url": "https://www.wallpaper.com/feed", "category": "カルチャー / ライフスタイル"},
    {"name": "The Guardian - Culture", "url": "https://www.theguardian.com/culture/rss", "category": "カルチャー / ライフスタイル"},
    {"name": "Aeon", "url": "https://aeon.co/feed.rss", "category": "カルチャー / ライフスタイル"},
    # --- テック / イノベーション ---
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "category": "テック / イノベーション"},
    {"name": "Fast Company", "url": "https://www.fastcompany.com/latest/rss", "category": "テック / イノベーション"},
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
        post_to_slack(f":earth_americas: *流行事象キャッチアップ - {today}*\n\n本日の新着トレンドはありませんでした。")
        return

    # スコアリング
    for a in all_articles:
        a["score"] = score_article(a)

    random.shuffle(all_articles)
    all_articles.sort(key=lambda a: a["score"], reverse=True)

    # カテゴリ別
    categories = {}
    for a in all_articles:
        cat = a["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(a)

    # 同一ソース最大2件
    for cat in categories:
        source_count = {}
        filtered = []
        for a in categories[cat]:
            count = source_count.get(a["source"], 0)
            if count < 2:
                source_count[a["source"]] = count + 1
                filtered.append(a)
        categories[cat] = filtered[:6]

    # Slackメッセージ構築
    cat_emoji = {
        "プロダクト / サービス": ":rocket:",
        "カルチャー / ライフスタイル": ":art:",
        "テック / イノベーション": ":bulb:",
    }
    cat_order = ["プロダクト / サービス", "カルチャー / ライフスタイル", "テック / イノベーション"]

    lines = [f":earth_americas: *流行事象キャッチアップ - {today}*\n"]

    for cat in cat_order:
        articles = categories.get(cat, [])
        if not articles:
            continue
        emoji = cat_emoji.get(cat, ":pushpin:")
        lines.append(f"*{emoji} {cat}*")
        for a in articles:
            lines.append(f"  <{a['link']}|{a['title']}>\n  _{a['source']}_")
        lines.append("")

    lines.append("今日も良い一日を :coffee:")

    total = sum(len(v) for v in categories.values())
    print(f"投稿件数: {total}件")

    message = "\n".join(lines)
    post_to_slack(message)
    print("Slack に投稿しました!")


if __name__ == "__main__":
    main()
