import discord
from discord.ext import commands
import re

EMOJI_REGEX = re.compile(r":([a-zA-Z0-9_]{2,32}):")

class NQN(commands.Cog):
    """Non-Nitro emoji replacement - only for animated emojis"""
    def __init__(self, bot):
        self.bot = bot
    
    async def get_or_create_webhook(self, channel):
        webhooks = await channel.webhooks()
        for wh in webhooks:
            if wh.name == "Flowy-NQN":
                return wh
        return await channel.create_webhook(name="Flowy-NQN")
    
    def has_nitro(self, member):
        """Check if user has Nitro by checking if they have a premium subscription"""
        # Check if user has animated avatar (reliable Nitro indicator)
        if member.display_avatar.is_animated():
            return True
        # Check premium_since (server boosting)
        if hasattr(member, 'premium_since') and member.premium_since:
            return True
        return False
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Check if message contains emoji shortcodes
        matches = EMOJI_REGEX.findall(message.content)
        if not matches:
            return
        
        guild_emojis = {e.name: e for e in message.guild.emojis}
        
        # Check if any matched emoji is animated
        has_animated_emoji = False
        for name in matches:
            if name in guild_emojis and guild_emojis[name].animated:
                has_animated_emoji = True
                break
        
        # Only trigger for animated emojis from non-Nitro users
        if not has_animated_emoji:
            return
        
        if self.has_nitro(message.author):
            return  # Let Nitro users use their own emojis
        
        new_content = message.content
        replaced = False
        
        for name in matches:
            if name in guild_emojis:
                emoji = guild_emojis[name]
                # Only replace animated emojis
                if emoji.animated:
                    tag = f"<a:{emoji.name}:{emoji.id}>"
                    new_content = new_content.replace(f":{name}:", tag)
                    replaced = True
        
        if not replaced:
            return
        
        webhook = await self.get_or_create_webhook(message.channel)
        
        await webhook.send(
            content=new_content,
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url
        )
        
        await message.delete()

async def setup(bot):
    await bot.add_cog(NQN(bot))
