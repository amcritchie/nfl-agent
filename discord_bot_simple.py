# Simple Discord bot test - just sends messages
from dotenv import load_dotenv
load_dotenv()

import os
import discord
from discord.ext import commands

# Debug: Print environment variables
print(f"DEBUG - DISCORD_TOKEN: {os.getenv('DISCORD_TOKEN')[:20]}..." if os.getenv('DISCORD_TOKEN') else "DEBUG - DISCORD_TOKEN: None")
print(f"DEBUG - TARGET_CHANNEL_ID: {os.getenv('TARGET_CHANNEL_ID')}")

# Discord bot setup - no privileged intents
intents = discord.Intents.default()
# intents.message_content = True  # Commented out to avoid privileged intent requirement
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Target channel ID: {TARGET_CHANNEL_ID}')
    
    # Send a test message when the bot starts up
    try:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            await channel.send("🤖 **NFL Agent Bot is online!**\n\nI'm ready to help with NFL questions!")
            print("✅ Test message sent successfully!")
        else:
            print(f"❌ Could not find channel with ID: {TARGET_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Error sending test message: {e}")

@bot.command(name='test')
async def test_command(ctx):
    """Simple test command"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
    
    await ctx.send("✅ Test command executed successfully!")

@bot.command(name='hello')
async def hello_command(ctx):
    """Say hello"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
    
    await ctx.send("👋 Hello! I'm your NFL agent bot!")

@bot.command(name='ping')
async def ping_command(ctx):
    """Test responsiveness"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
    
    await ctx.send("🏓 Pong! Bot is responsive!")

def run_discord_bot():
    """Run the Discord bot"""
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables")
        return
    
    if TARGET_CHANNEL_ID == 0:
        print("ERROR: TARGET_CHANNEL_ID not found in environment variables")
        return
    
    try:
        print("Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Error running Discord bot: {e}")

if __name__ == "__main__":
    run_discord_bot()
