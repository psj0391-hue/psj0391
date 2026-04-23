import feedparser
import requests
import re
from bs4 import BeautifulSoup

BLOG_ID = "namanama-"
RSS_URL = f"https://rss.blog.naver.com/{BLOG_ID}"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def get_blog_fulltext(post_link):
    post_id = re.search(r'/(\d+)', post_link)
    if not post_id:
        return ""
    mobile_url = f"https://m.blog.naver.com/{BLOG_ID}/{post_id.group(1)}"
    try:
        res = requests.get(mobile_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        lines = [l.strip() for l in soup.get_text(separator='\n').splitlines() if l.strip()]
        return '\n'.join(lines)
    except Exception as e:
        print(f"본문 추출 실패: {e}")
        return ""


def get_latest_post(direct_url=None):
    if direct_url:
        post_link = direct_url
        fulltext  = get_blog_fulltext(post_link)
        title = fulltext.split("\n")[0] if fulltext else "블로그 글"
        return {
            "title": title,
            "link": post_link,
            "summary": "\n".join(fulltext.split("\n")[:20]),
            "fulltext": fulltext,
            "published": "",
        }

    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        print("블로그 글을 가져올 수 없습니다.")
        return None

    latest = feed.entries[0]
    post_link = latest.get("link", "")
    fulltext = get_blog_fulltext(post_link)

    post = {
        "title": latest.get("title", ""),
        "link": post_link,
        "summary": latest.get("summary", ""),
        "fulltext": fulltext,
        "published": latest.get("published", ""),
    }

    print(f"최신 글 제목: {post['title']}")
    print(f"본문 길이: {len(fulltext)}자")
    return post
