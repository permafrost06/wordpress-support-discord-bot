import discord
import requests
import asyncio
from os import getenv
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from wp import get_threads, get_posts
from markdownify import markdownify
import json

load_dotenv()

TOKEN = getenv("WP_BOT_TOKEN")
CHANNEL_ID = getenv("TABLEBERG_CHANNEL_ID")
WEBHOOK_URL = getenv("TABLEBERG_SUPPORT_WEBHOOK")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Store posted topics to avoid duplicates
posted_threads = set()

async def check_threads():
    """Periodically check for new threads and post them in Discord."""
    await client.wait_until_ready()
    channel = await client.fetch_channel(CHANNEL_ID)
    
    while not client.is_closed():
        thread_links = get_threads()
        thread_links.reverse()

        with open('data.json', 'r') as fp:
            old_threads = json.load(fp)

        threads = {}
        
        print("links received")
        for link in thread_links:
            print("parsing thread")
            thread_details = get_posts(link)

            if not link in old_threads.keys():
                print("creating new thread")
                content = f'[Link to thread](<{link}>)\n\n' + markdownify(thread_details['topic_text'])
                thread = await channel.create_thread(name=thread_details['topic_title'], type=discord.ChannelType.public_thread)
                send_webhook_message_in_thread(thread.id, thread_details['topic_author'], content)
            else:
                print("skipping existing thread")
                thread = await client.fetch_channel(old_threads[link]['id'])

            thread_details["id"] = thread.id

            print("posting replies")
            for reply in thread_details['replies']:
                def match_reply(old_reply):
                    if reply['id'] == old_reply['id']:
                        return True

                if link in old_threads.keys():
                    if len(list(filter(match_reply, old_threads[link]['replies']))) > 0:
                        print("skipping existing reply")
                        continue

                print("posting new reply")
                username = reply['username'].split("(@")[1].split(")")[0]
                send_webhook_message_in_thread(thread.id, username, markdownify(reply['content']))

            threads[link] = thread_details
            await asyncio.sleep(5)

        print("dumping new threads data")
        with open('data.json', 'w') as fp:
            json.dump(threads, fp)
    
        print("all links done. sleeping for 10 minutes.")
        await asyncio.sleep(60*10)  # Wait 1 minute before checking again

def send_webhook_message_in_thread(thread_id, username, content):
    """Send a webhook message inside the created thread."""
    url = f"{WEBHOOK_URL}?thread_id={thread_id}"  # Append thread_id as query parameter
    payload = {
        "username": username,  # Custom name
        "content": content
    }
    response = requests.post(url, json=payload)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_threads())  # Start the thread-checking task

client.run(TOKEN)

