import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional

class MassPing(commands.Cog):
    """Mass ping users (use responsibly)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_masspings = set()  # Prevent multiple simultaneous masspings
    
    @app_commands.command(name="massping", description="Ping a user multiple times (Admin only)")
    @app_commands.describe(
        user="User to ping",
        count="Number of times to ping (max 50)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def massping(self, interaction: discord.Interaction, user: discord.Member, count: int):
        """Mass ping a user"""
        
        # Validate count
        if count < 1:
            await interaction.response.send_message("❌ Count must be at least 1!", ephemeral=True)
            return
        
        if count > 50:
            await interaction.response.send_message("❌ Count cannot exceed 50 (Discord rate limits)!", ephemeral=True)
            return
        
        # Check if user is bot owner or has higher role
        if user.top_role >= interaction.user.top_role and user != interaction.user:
            await interaction.response.send_message("❌ You cannot mass ping someone with equal or higher role!", ephemeral=True)
            return
        
        # Check if already running
        if user.id in self.active_masspings:
            await interaction.response.send_message(f"❌ Already mass pinging {user.mention}!", ephemeral=True)
            return
        
        # Confirm
        await interaction.response.send_message(
            f"🔔 Starting mass ping on {user.mention} ({count} times)...",
            ephemeral=True
        )
        
        self.active_masspings.add(user.id)
        
        try:
            for i in range(count):
                try:
                    await interaction.channel.send(f"{user.mention}")
                    await asyncio.sleep(0.5)  # 500ms delay to avoid rate limits
                except discord.HTTPException:
                    await asyncio.sleep(2)  # If rate limited, wait longer
                    continue
                except Exception as e:
                    print(f"Error in massping: {e}")
                    break
            
            await interaction.followup.send(f"✅ Finished pinging {user.mention} {count} times!", ephemeral=True)
        
        finally:
            self.active_masspings.discard(user.id)
    
    @app_commands.command(name="massping-stop", description="Stop an ongoing mass ping (Admin only)")
    @app_commands.describe(user="User whose mass ping to stop")
    @app_commands.checks.has_permissions(administrator=True)
    async def massping_stop(self, interaction: discord.Interaction, user: discord.Member):
        """Stop mass pinging a user"""
        
        if user.id in self.active_masspings:
            self.active_masspings.discard(user.id)
            await interaction.response.send_message(f"⏹️ Stopped mass pinging {user.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ No active mass ping for {user.mention}!", ephemeral=True)
    
    @massping.error
    @massping_stop.error
    async def massping_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(MassPing(bot))
