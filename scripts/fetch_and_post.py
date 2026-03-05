import json
import urllib.request
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# PdM / プロダクトマネジメント関連のRSSフィード
RSS_FEEDS = [
    {
        "name": "ProductZine",
        "url": "https://productzine.jp/feed/rss2",
        "category": "PdM全般",
    },
    {
        "name": "note #プロダクトマネージャー",
        "url": "https://note.com/hashtag/%E3%83%97%E3%83%AD%E3%83%80%E3%82%AF%E3%83%88%E3%83%9E%E3%83%8D%E3%83%BC%E3%82%B8%E3%83%A3%E3%83%BC?f=new&rss",
        "category": "PdM全般",
    },
    {
        "name": "note #プロダクトマネジメント",
        "url": "https://note.com/hashtag/%E3%83%97%E3%83%AD%E3%83%80%E3%82%AF%E3%83%88%E3%83%9E%E3%83%8D%E3%82%B8%E3%83%A1%E3%83%B3%E3%83%88?f=new&rss",
        "category": "PdM全般",
    },
    {
        "name": "note #AI活用",
        "url": "https://note.com/hashtag/AI%E6%B4%BB%E7%94%A8?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "note #Claude",
        "url": "https://note.com/hashtag/Claude?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "Zenn - プロダクトマネジメント",
        "url": "https://zenn.dev/topics/productmanagement/feed",
        "category": "PdM全般",
    },
    {
        "name": "Zenn - AI",
        "url": "https://zenn.dev/topics/ai/feed",
        "category": "AI x PdM",
    },
]

# 重複排除用
seen_titles = set()


def fetch_rss(feed):
    """RSSフィードから直近24時間以内の記事を取得"""
    articles = []
    try:
        req = urllib.request.Request(
            feed["url"],
            headers={"User-Agent": "PDM-Morning-News-Bot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()

        root = ET.fromstring(data)

        # RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "")

            if not title or not link:
                continue
            if title in seen_titles:
                continue

            seen_titles.add(title)
            articles.append(
                {
                    "title": title,
                    "link": link,
                    "source": feed["name"],
                    "category": feed["category"],
                }
            )

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
            if title in seen_titles:
                continue

            seen_titles.add(title)
            articles.append(
                {
                    "title": title,
                    "link": link,
                    "source": feed["name"],
                    "category": feed["category"],
                }
            )

    except Exception as e:
        print(f"[WARN] {feed['name']} の取得に失敗: {e}")

    return articles[:5]  # 各フィードから最大5件


def post_to_slack(message):
    """Slack Webhook にメッセージを送信"""
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

    all_articles = []
    for feed in RSS_FEEDS:
        articles = fetch_rss(feed)
        all_articles.extend(articles)

    if not all_articles:
        post_to_slack(f":newspaper: *PdM朝刊 - {today}*\n\n本日の新着記事はありませんでした。")
        return

    # カテゴリ別に分類
    pdm_articles = [a for a in all_articles if a["category"] == "PdM全般"]
    ai_articles = [a for a in all_articles if a["category"] == "AI x PdM"]

    lines = [f":newspaper: *PdM朝刊 - {today}*\n"]

    if pdm_articles:
        lines.append("*-- PdM / プロダクトマネジメント --*")
        for a in pdm_articles[:5]:
            lines.append(f"  <{a['link']}|{a['title']}>\n  _{a['source']}_")
        lines.append("")

    if ai_articles:
        lines.append("*-- AI x PdM / AI活用 --*")
        for a in ai_articles[:5]:
            lines.append(f"  <{a['link']}|{a['title']}>\n  _{a['source']}_")
        lines.append("")

    lines.append("今日も良い一日を :coffee:")

    message = "\n".join(lines)
    post_to_slack(message)
    print("Slack に投稿しました!")


if __name__ == "__main__":
    main()
