import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os

CONFESSIONS_LOG_FILE = "confessions_log.txt"

class Confessions(commands.Cog):
    """Anonymous confession system with automatic logging"""
    
    def __init__(self, bot):
        self.bot = bot
        self.confession_channels = {}  # guild_id: channel_id mapping
    
    @app_commands.command(name="confess", description="Submit an anonymous confession")
    @app_commands.describe(confession="Your anonymous confession")
    async def confess(self, interaction: discord.Interaction, confession: str):
        """Submit an anonymous confession"""
        
        guild_id = interaction.guild.id
        
        # Check if confession channel is set for this guild
        if guild_id not in self.confession_channels:
            await interaction.response.send_message(
                "No confession channel has been set up!\n"
                "Ask an admin to use `/confession-setup` first.",
                ephemeral=True
            )
            return
        
        channel_id = self.confession_channels[guild_id]
        confession_channel = interaction.guild.get_channel(channel_id)
        
        if not confession_channel:
            await interaction.response.send_message(
                "Confession channel not found! Please ask an admin to set it up again.",
                ephemeral=True
            )
            return
        
        # Log the confession with ALL user details
        log_entry = (
            f"\n{'='*80}\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"User: {interaction.user.name}#{interaction.user.discriminator}\n"
            f"User ID: {interaction.user.id}\n"
            f"Display Name: {interaction.user.display_name}\n"
            f"Guild: {interaction.guild.name} (ID: {interaction.guild.id})\n"
            f"Channel Used: #{interaction.channel.name} (ID: {interaction.channel.id})\n"
            f"Confession:\n{confession}\n"
            f"{'='*80}\n"
        )
        
        # Append to log file automatically
        with open(CONFESSIONS_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Send confession anonymously to confession channel
        embed = discord.Embed(
            title="Anonymous Confession",
            description=confession,
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="This confession was submitted anonymously")
        
        try:
            await confession_channel.send(embed=embed)
            await interaction.response.send_message(
                "Your confession has been submitted anonymously!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send messages in the confession channel!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Error sending confession: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="confession-setup", description="Set up confession channel (Admin only)")
    @app_commands.describe(channel="Channel where confessions will be posted")
    @app_commands.checks.has_permissions(administrator=True)
    async def confession_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set up the confession channel for the server"""
        
        guild_id = interaction.guild.id
        self.confession_channels[guild_id] = channel.id
        
        await interaction.response.send_message(
            f"Confession channel set to {channel.mention}!\n"
            f"Users can now use `/confess [confession:]` to submit anonymous confessions.\n"
            f"All confessions are automatically logged to `{CONFESSIONS_LOG_FILE}` with user details.",
            ephemeral=True
        )
    
    @confession_setup.error
    async def confession_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You need Administrator permissions to use this command!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Confessions(bot))
