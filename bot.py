import discord
from discord.ext import commands
import asyncio
import os
from keep_alive import keep_alive

# Get token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN environment variable not set!")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user}')
    print(f'Bot ID: {bot.user.id}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# Load all cogs
async def load_cogs():
    cog_files = ['messaging', 'roles', 'emojis', 'nqn', 'confessions', 'moderation', 'leveling', 'massping']
    for cog in cog_files:
        try:
            await bot.load_extension(f'cogs.{cog}')
            print(f'✅ Loaded cog: {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')

async def main():
    # Start Flask web server for UptimeRobot
    keep_alive()
    
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
