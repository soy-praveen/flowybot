import discord
from discord.ext import commands
import os
import asyncio

EMOJI_FOLDER = r"C:\Users\yosoy\OneDrive\Desktop\Kirito crib\Flowy\emojis"
VALID_EXTS = (".png", ".jpg", ".gif")

class Emojis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if "addemotes" not in message.content.lower():
            return
        
        guild = message.guild
        if guild is None:
            return
        
        if not guild.me.guild_permissions.manage_emojis_and_stickers:
            await message.channel.send("❌ Missing Manage Emojis permission.")
            return
        
        existing_names = {e.name for e in guild.emojis}
        
        emoji_files = sorted(
            f for f in os.listdir(EMOJI_FOLDER)
            if f.lower().endswith(VALID_EXTS)
        )
        
        added = 0
        skipped = 0
        
        for index, file in enumerate(emoji_files, start=1):
            emoji_name = f"emoji_{index}"
            
            if emoji_name in existing_names:
                skipped += 1
                continue
            
            if len(guild.emojis) >= guild.emoji_limit:
                await message.channel.send("⚠️ Emoji limit reached.")
                break
            
            try:
                with open(os.path.join(EMOJI_FOLDER, file), "rb") as img:
                    await guild.create_custom_emoji(
                        name=emoji_name,
                        image=img.read()
                    )
                    added += 1
                    existing_names.add(emoji_name)
                    await asyncio.sleep(1.5)
            except discord.HTTPException as e:
                print(f"Failed to add {file}: {e}")
        
        await message.channel.send(
            f"✅ Added: {added} | ⏭️ Skipped: {skipped}"
        )

async def setup(bot):
    await bot.add_cog(Emojis(bot))
