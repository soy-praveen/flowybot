import discord
from discord import app_commands
from discord.ext import commands

class Messaging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="msg", description="Send a message in the channel")
    @app_commands.describe(
        embed="Send as embed? (yes/no)",
        message="The message to send"
    )
    async def msg(self, interaction: discord.Interaction, embed: str, message: str):
        """Send a message in the channel, optionally as an embed."""
        
        if embed.lower() in ["yes", "y", "true", "1"]:
            embed_msg = discord.Embed(
                description=message,
                color=discord.Color.blue()
            )
            await interaction.response.send_message("✅ Message sent!", ephemeral=True)
            await interaction.channel.send(embed=embed_msg)
        else:
            await interaction.response.send_message("✅ Message sent!", ephemeral=True)
            await interaction.channel.send(message)

async def setup(bot):
    await bot.add_cog(Messaging(bot))
