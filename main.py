import discord
import requests
import asyncio
import json
from os import getenv, path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from wp import get_threads, get_posts
from markdownify import markdownify
import argparse

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
parser.add_argument('--verbose', action='store_true', help='Print logging')

args = parser.parse_args()

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
    if args.verbose:
        print(f"starting {product}")
    data_filename = f'{product}-data.json'

    if not path.exists(data_filename):
        with open(data_filename, 'w') as file:
            file.write('{}')

    with open(data_filename, 'r') as fp:
        old_threads = json.load(fp)

    if args.verbose:
        print("data file loaded")

    thread_links = get_threads(SUPPORT_URL)
    thread_links.reverse()

    threads = {}
    
    channel = await client.fetch_channel(CHANNEL_ID)

    if args.verbose:
        print("links received")
    await asyncio.sleep(30)
    for thread_obj in thread_links:
        link = thread_obj["link"]
        last_updated = thread_obj["last_updated"]

        if link in old_threads.keys():
            if "last_updated" in old_threads[link]:
                if old_threads[link]["last_updated"] == last_updated:
                    if args.verbose:
                        print("thread hasn't updated")
                    continue

        if args.verbose:
            print("parsing thread")
        thread_details = get_posts(link)

        if not link in old_threads.keys():
            content = f'[Link to thread](<{link}>)\n\n' + markdownify(thread_details['topic_text'])
            if not args.dry_run:
                if args.verbose:
                    print("creating new thread")
                thread = await channel.create_thread(name=thread_details['topic_title'], type=discord.ChannelType.public_thread)
                send_webhook_message_in_thread(thread.id, thread_details['topic_author'], content, WEBHOOK_URL)
            else:
                print(f"create thread:")
                print(f"name: {thread_details['topic_title']}")
                print(f"author: {thread_details['topic_author']}, content: {content[0:100]}")
        else:
            if args.verbose:
                print("skipping existing thread")
            thread = await client.fetch_channel(old_threads[link]['id'])

        if not args.dry_run:
            thread_details["id"] = thread.id

        if args.verbose:
            print("posting replies")
        for reply_id in thread_details['replies']:
            reply = thread_details['replies'][reply_id]

            if link in old_threads.keys():
                if reply_id in old_threads[link]['replies']:
                    continue

            if args.verbose:
                print("posting new reply")
            username = reply['username'].split("(@")[1].split(")")[0]
            if not args.dry_run:
                send_webhook_message_in_thread(thread.id, username, markdownify(reply['content']), WEBHOOK_URL)
            else:
                print(f"create reply {reply_id}:")
                print(f"author: {username}, content: {markdownify(reply['content'][0:100])}")

        thread_details["last_updated"] = last_updated
        threads[link] = thread_details
        await asyncio.sleep(60)

    if args.verbose:
        print("dumping new threads data")
    if not args.dry_run:
        with open(data_filename, 'w') as fp:
            json.dump(threads, fp)

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
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(main_loop())

client.run(TOKEN)
