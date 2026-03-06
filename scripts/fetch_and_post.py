import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 設定ファイル読み込み
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = json.load(f)

BOOST_KEYWORDS = [k.lower() for k in CONFIG.get("boost_keywords", [])]
NG_KEYWORDS = [k.lower() for k in CONFIG.get("ng_keywords", [])]
NG_SOURCES = [s.lower() for s in CONFIG.get("ng_sources", [])]
BOOST_SOURCES = [s.lower() for s in CONFIG.get("boost_sources", [])]

# 記事の合計上限
MAX_ARTICLES = 20

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
        "url": "https://markezine.jp/article/feed.xml",
        "category": "PdM全般",
    },
    {
        "name": "Web担当者Forum",
        "url": "https://webtan.impress.co.jp/feed",
        "category": "PdM全般",
    },
    {
        "name": "SELECK",
        "url": "https://seleck.cc/feed",
        "category": "PdM全般",
    },
    {
        "name": "LogMi Tech",
        "url": "https://logmi.jp/tech/feed",
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
    # --- はてブ人気エントリー（話題の記事） ---
    {
        "name": "はてブ - テクノロジー",
        "url": "https://b.hatena.ne.jp/hotentry/it.rss",
        "category": "PdM全般",
    },
    {
        "name": "はてブ - マーケティング",
        "url": "https://b.hatena.ne.jp/search/tag?q=%E3%83%9E%E3%83%BC%E3%82%B1%E3%83%86%E3%82%A3%E3%83%B3%E3%82%B0&mode=rss&sort=popular",
        "category": "PdM全般",
    },
    {
        "name": "はてブ - プロダクトマネジメント",
        "url": "https://b.hatena.ne.jp/search/tag?q=%E3%83%97%E3%83%AD%E3%83%80%E3%82%AF%E3%83%88%E3%83%9E%E3%83%8D%E3%82%B8%E3%83%A1%E3%83%B3%E3%83%88&mode=rss&sort=popular",
        "category": "PdM全般",
    },
    {
        "name": "はてブ - ChatGPT",
        "url": "https://b.hatena.ne.jp/search/tag?q=ChatGPT&mode=rss&sort=popular",
        "category": "AI x PdM",
    },
    {
        "name": "はてブ - Claude",
        "url": "https://b.hatena.ne.jp/search/tag?q=Claude&mode=rss&sort=popular",
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


def fetch_hatena_bookmarks(articles):
    """はてなブックマーク数APIで各記事のブックマーク数を一括取得"""
    if not articles:
        return {}
    bookmark_counts = {}
    # APIは1回につき50URLまで対応
    batch_size = 50
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        params = "&".join(
            f"url={urllib.parse.quote(a['link'], safe='')}" for a in batch
        )
        api_url = f"https://bookmark.hatenaapis.com/count/entries?{params}"
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "PDM-Morning-News-Bot/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                bookmark_counts.update(data)
        except Exception as e:
            print(f"[WARN] はてブ数の取得に失敗: {e}")
    return bookmark_counts


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

    # NGソース・NGキーワードでフィルタ
    all_articles = [
        a for a in all_articles
        if a["source"].lower() not in NG_SOURCES
        and not any(ng in a["title"].lower() for ng in NG_KEYWORDS)
    ]

    # はてブ数を取得して人気度を測定
    bookmark_counts = fetch_hatena_bookmarks(all_articles)

    # スコアリング: boost_keywords/boost_sources + はてブ数で加点
    def score(article):
        s = 0
        title_lower = article["title"].lower()
        source_lower = article["source"].lower()
        for kw in BOOST_KEYWORDS:
            if kw in title_lower:
                s += 2
        if source_lower in BOOST_SOURCES:
            s += 1
        # はてブ数による加点
        bookmarks = bookmark_counts.get(article["link"], 0)
        article["bookmarks"] = bookmarks
        if bookmarks >= 100:
            s += 5
        elif bookmarks >= 50:
            s += 4
        elif bookmarks >= 20:
            s += 3
        elif bookmarks >= 10:
            s += 2
        elif bookmarks >= 3:
            s += 1
        return s

    for a in all_articles:
        a["score"] = score(a)

    # カテゴリ別に分類し、スコア順にソート
    import random
    random.shuffle(all_articles)  # 同スコア内でランダム性を持たせる
    all_articles.sort(key=lambda a: a["score"], reverse=True)

    pdm_articles = [a for a in all_articles if a["category"] == "PdM全般"]
    ai_articles = [a for a in all_articles if a["category"] == "AI x PdM"]

    # ソースの偏りを防ぐ: 同一ソースから最大2件
    def dedupe_sources(articles, max_per_source=2):
        source_count = {}
        result = []
        for a in articles:
            count = source_count.get(a["source"], 0)
            if count < max_per_source:
                source_count[a["source"]] = count + 1
                result.append(a)
        return result

    pdm_articles = dedupe_sources(pdm_articles)
    ai_articles = dedupe_sources(ai_articles)

    # 合計20件に収める（PdM 10件 + AI 10件を目安に）
    half = MAX_ARTICLES // 2
    pdm_pick = pdm_articles[:half]
    ai_pick = ai_articles[:half]
    if len(pdm_pick) < half:
        ai_pick = ai_articles[: MAX_ARTICLES - len(pdm_pick)]
    if len(ai_pick) < half:
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
