import discord
import requests
import asyncio
import json
from os import getenv, path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from wp import get_threads, get_posts
from markdownify import markdownify

load_dotenv()

TOKEN = getenv("WP_BOT_TOKEN")

tableberg_support_url = "https://wordpress.org/support/plugin/tableberg/"
tableberg_channel = getenv("TABLEBERG_CHANNEL_ID")
tableberg_webhook = getenv("TABLEBERG_SUPPORT_WEBHOOK")

ub_support_url = "https://wordpress.org/support/plugin/ultimate-blocks/"
ub_channel = getenv("UB_CHANNEL_ID")
ub_webhook = getenv("UB_SUPPORT_WEBHOOK")

wptb_support_url = "https://wordpress.org/support/plugin/wp-table-builder/"
wptb_channel = getenv("WPTB_CHANNEL_ID")
wptb_webhook = getenv("WPTB_SUPPORT_WEBHOOK")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

posted_threads = set()

async def check_threads(product, SUPPORT_URL, CHANNEL_ID, WEBHOOK_URL):
    data_filename = f'{product}-data.json'

    if not path.exists(data_filename):
        with open(data_filename, 'w') as file:
            file.write('{}')

    with open(data_filename, 'r') as fp:
        old_threads = json.load(fp)

    print("old file loaded")

    thread_links = get_threads(SUPPORT_URL)
    thread_links.reverse()

    threads = {}
    
    channel = await client.fetch_channel(CHANNEL_ID)

    print("links received")
    await asyncio.sleep(5)
    for link in thread_links:
        print("parsing thread")
        thread_details = get_posts(link)

        if not link in old_threads.keys():
            print("creating new thread")
            content = f'[Link to thread](<{link}>)\n\n' + markdownify(thread_details['topic_text'])
            thread = await channel.create_thread(name=thread_details['topic_title'], type=discord.ChannelType.public_thread)
            send_webhook_message_in_thread(thread.id, thread_details['topic_author'], content, WEBHOOK_URL)
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
            send_webhook_message_in_thread(thread.id, username, markdownify(reply['content']), WEBHOOK_URL)

        threads[link] = thread_details
        await asyncio.sleep(5)

    print("dumping new threads data")
    with open(data_filename, 'w') as fp:
        json.dump(threads, fp)

    print("all links done. sleeping for 1 minute.")

def send_webhook_message_in_thread(thread_id, username, content, WEBHOOK_URL):
    url = f"{WEBHOOK_URL}?thread_id={thread_id}"
    payload = {
        "username": username,
        "content": content
    }
    response = requests.post(url, json=payload)

async def main_loop():
    await client.wait_until_ready()
    
    while not client.is_closed():
        await check_threads("tableberg", tableberg_support_url, tableberg_channel, tableberg_webhook)
        await asyncio.sleep(60)
        await check_threads("ub", ub_support_url, ub_channel, ub_webhook)
        await asyncio.sleep(60)
        await check_threads("wptb", wptb_support_url, wptb_channel, wptb_webhook)
        print("all products done. sleeping for 10 minutes.")
        await asyncio.sleep(60*10)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(main_loop())

client.run(TOKEN)
