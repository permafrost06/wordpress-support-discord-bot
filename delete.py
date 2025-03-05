import discord
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("WP_BOT_TOKEN")

# Enable necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    """Listens for the !clear command to delete all messages in the channel."""
    if message.content == "!clear" and message.author.guild_permissions.manage_messages:
        channel = message.channel

        await message.channel.send("Deleting messages...", delete_after=2)
        await asyncio.sleep(2)  # Allow time for users to see the message

        # Fetch and delete messages
        messages = [msg async for msg in channel.history(limit=None)]

        for msg in messages:
            try:
                await msg.delete()
                await asyncio.sleep(1)  # Prevent rate limiting
            except discord.Forbidden:
                await channel.send("I don't have permission to delete messages.")
                return
            except discord.HTTPException:
                await channel.send("Failed to delete some messages.")
                return

        await channel.send("All messages have been deleted!", delete_after=5)

client.run(TOKEN)

