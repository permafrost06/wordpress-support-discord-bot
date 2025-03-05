import requests
from bs4 import BeautifulSoup
import time

SUPPORT_URL = "https://wordpress.org/support/plugin/tableberg/"

def get_soup(url):
    """Fetch the page content and return a BeautifulSoup object."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return BeautifulSoup(response.text, "html.parser")

def get_threads():
    soup = get_soup(SUPPORT_URL)
    topic_links = [a["href"] for a in soup.select(".bbp-body .bbp-topic-permalink")]

    if not topic_links:
        return []

    return topic_links

def get_posts(topic_url):
    topic_soup = get_soup(topic_url)
    for elem in topic_soup.select(".bbp-topic-revision-log"):
        elem.decompose()

    topic_title = topic_soup.select_one(".page-title").get_text(strip=True)
    topic_author = topic_soup.select_one(".bbp-lead-topic .bbp-author-name").get_text(strip=True)
    topic_text = topic_soup.select_one(".bbp-topic-content").decode_contents()

    replies = []
    for reply in topic_soup.select(".bbp-replies .reply"):
        reply_id = reply.get("id").split("post-")[1]
        reply_author = reply.select_one(".bbp-author-name").get_text(strip=True)
        reply_username = reply.select_one(".bbp-user-nicename").get_text(strip=True)
        reply_content = reply.select_one(".bbp-reply-content").decode_contents()
        replies.append({
            "id": reply_id,
            "author": reply_author,
            "username": reply_username,
            "content": reply_content
        })

    return {
        'topic_title': topic_title,
        'topic_author': topic_author,
        'topic_text': topic_text,
        'replies': replies
    }
