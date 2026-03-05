import json
import urllib.request
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 記事の合計上限
MAX_ARTICLES = 5

# PdM / プロダクトマネジメント関連のRSSフィード
RSS_FEEDS = [
    # --- PdM全般 ---
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
        "name": "Qiita - プロダクトマネジメント",
        "url": "https://qiita.com/tags/productmanagement/feed",
        "category": "PdM全般",
    },
    {
        "name": "Zenn - プロダクトマネジメント",
        "url": "https://zenn.dev/topics/productmanagement/feed",
        "category": "PdM全般",
    },
    {
        "name": "MarkeZine",
        "url": "https://markezine.jp/rss/new/20/index.xml",
        "category": "PdM全般",
    },
    {
        "name": "ferret",
        "url": "https://ferret-plus.com/feed",
        "category": "PdM全般",
    },
    {
        "name": "UX MILK",
        "url": "https://uxmilk.jp/feed",
        "category": "PdM全般",
    },
    # --- AI x PdM / AI業務活用 ---
    {
        "name": "note #ClaudeCode",
        "url": "https://note.com/hashtag/ClaudeCode?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "note #Claude",
        "url": "https://note.com/hashtag/Claude?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "note #AI業務効率化",
        "url": "https://note.com/hashtag/AI%E6%A5%AD%E5%8B%99%E5%8A%B9%E7%8E%87%E5%8C%96?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "note #AI自動化",
        "url": "https://note.com/hashtag/AI%E8%87%AA%E5%8B%95%E5%8C%96?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "note #生成AI活用",
        "url": "https://note.com/hashtag/%E7%94%9F%E6%88%90AI%E6%B4%BB%E7%94%A8?f=new&rss",
        "category": "AI x PdM",
    },
    {
        "name": "Zenn - Claude",
        "url": "https://zenn.dev/topics/claude/feed",
        "category": "AI x PdM",
    },
    {
        "name": "Zenn - AIエージェント",
        "url": "https://zenn.dev/topics/agent/feed",
        "category": "AI x PdM",
    },
    {
        "name": "Qiita - Claude",
        "url": "https://qiita.com/tags/claude/feed",
        "category": "AI x PdM",
    },
    {
        "name": "Hatena - AI業務活用",
        "url": "https://b.hatena.ne.jp/search/tag?q=AI+%E6%A5%AD%E5%8B%99&mode=rss",
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

    return articles[:3]  # 各フィードから最大3件


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

    # カテゴリ別に分類し、ソースが偏らないようシャッフル
    import random
    random.shuffle(all_articles)

    pdm_articles = [a for a in all_articles if a["category"] == "PdM全般"]
    ai_articles = [a for a in all_articles if a["category"] == "AI x PdM"]

    # ソースの偏りを防ぐ: 同一ソースから最大1件
    def dedupe_sources(articles):
        seen_sources = set()
        result = []
        for a in articles:
            if a["source"] not in seen_sources:
                seen_sources.add(a["source"])
                result.append(a)
        return result

    pdm_articles = dedupe_sources(pdm_articles)
    ai_articles = dedupe_sources(ai_articles)

    # 合計5件に収める（PdM 3件 + AI 2件を目安に）
    pdm_pick = pdm_articles[:3]
    ai_pick = ai_articles[:2]
    if len(pdm_pick) < 3:
        ai_pick = ai_articles[: MAX_ARTICLES - len(pdm_pick)]
    if len(ai_pick) < 2:
        pdm_pick = pdm_articles[: MAX_ARTICLES - len(ai_pick)]

    lines = [f":newspaper: *PdM朝刊 - {today}*\n"]

    if pdm_pick:
        lines.append("*-- PdM / プロダクトマネジメント --*")
        for a in pdm_pick:
            lines.append(f"  <{a['link']}|{a['title']}>\n  _{a['source']}_")
        lines.append("")

    if ai_pick:
        lines.append("*-- AI x PdM / AI活用 --*")
        for a in ai_pick:
            lines.append(f"  <{a['link']}|{a['title']}>\n  _{a['source']}_")
        lines.append("")

    lines.append("今日も良い一日を :coffee:")

    message = "\n".join(lines)
    post_to_slack(message)
    print("Slack に投稿しました!")


if __name__ == "__main__":
    main()
