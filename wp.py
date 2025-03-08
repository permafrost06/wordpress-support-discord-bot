import requests
from bs4 import BeautifulSoup
import time

def get_soup(url):
    """Fetch the page content and return a BeautifulSoup object."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return BeautifulSoup(response.text, "html.parser")

def get_threads(SUPPORT_URL):
    soup = get_soup(SUPPORT_URL)
    topics_soup = soup.select(".bbp-body .topic")

    topics = []

    for topic_soup in topics_soup:
        topics.append({
            "link": topic_soup.select_one(".bbp-topic-permalink")["href"],
            "last_updated": topic_soup.select_one(".bbp-topic-freshness").select_one("a")["title"]
        })

    return topics

def get_posts(topic_url):
    topic_soup = get_soup(topic_url)
    for elem in topic_soup.select(".bbp-topic-revision-log"):
        elem.decompose()

    topic_title = topic_soup.select_one(".page-title").get_text(strip=True)
    topic_author = topic_soup.select_one(".bbp-lead-topic .bbp-author-name").get_text(strip=True)
    topic_text = topic_soup.select_one(".bbp-topic-content").decode_contents()

    replies = {}
    for reply in topic_soup.select(".bbp-replies .reply"):
        reply_id = reply.get("id").split("post-")[1]
        reply_author = reply.select_one(".bbp-author-name").get_text(strip=True)
        reply_username = reply.select_one(".bbp-user-nicename").get_text(strip=True)
        reply_content = reply.select_one(".bbp-reply-content").decode_contents()
        replies[reply_id] = {
            "author": reply_author,
            "username": reply_username,
            "content": reply_content
        }

    return {
        'topic_title': topic_title,
        'topic_author': topic_author,
        'topic_text': topic_text,
        'replies': replies
    }
