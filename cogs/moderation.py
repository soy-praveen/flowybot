import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
from typing import Optional

class Moderation(commands.Cog):
    """Moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="timeout", description="Timeout/mute a member (Mod only)")
    @app_commands.describe(
        member="Member to timeout",
        duration="Duration in minutes",
        reason="Reason for timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member, 
        duration: int,
        reason: Optional[str] = "No reason provided"
    ):
        """Timeout a member for specified duration in minutes"""
        
        # Can't timeout yourself
        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't timeout yourself!", ephemeral=True)
            return
        
        # Can't timeout bots
        if member.bot:
            await interaction.response.send_message("❌ You can't timeout bots!", ephemeral=True)
            return
        
        # Can't timeout server owner
        if member.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ You can't timeout the server owner!", ephemeral=True)
            return
        
        # Check role hierarchy
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't timeout someone with a higher or equal role!", ephemeral=True)
            return
        
        # Discord timeout limit is 28 days
        if duration > 40320:  # 28 days in minutes
            await interaction.response.send_message("❌ Timeout duration can't exceed 28 days (40320 minutes)!", ephemeral=True)
            return
        
        try:
            await member.timeout(timedelta(minutes=duration), reason=f"{reason} | By: {interaction.user}")
            
            embed = discord.Embed(
                title="⏱️ Member Timed Out",
                description=f"{member.mention} has been timed out",
                color=discord.Color.orange()
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this member!", ephemeral=True)
    
    @app_commands.command(name="untimeout", description="Remove timeout from a member (Mod only)")
    @app_commands.describe(
        member="Member to remove timeout from",
        reason="Reason for removing timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        """Remove timeout from a member"""
        
        if not member.is_timed_out():
            await interaction.response.send_message(f"❌ {member.mention} is not timed out!", ephemeral=True)
            return
        
        try:
            await member.timeout(None, reason=f"{reason} | By: {interaction.user}")
            await interaction.response.send_message(f"✅ Removed timeout from {member.mention}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to remove timeout!", ephemeral=True)
    
    @app_commands.command(name="kick", description="Kick a member from the server (Mod only)")
    @app_commands.describe(
        member="Member to kick",
        reason="Reason for kick"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        """Kick a member from the server"""
        
        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't kick yourself!", ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message("❌ You can't kick bots!", ephemeral=True)
            return
        
        if member.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ You can't kick the server owner!", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't kick someone with a higher or equal role!", ephemeral=True)
            return
        
        try:
            await member.kick(reason=f"{reason} | By: {interaction.user}")
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked from the server",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this member!", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server (Mod only)")
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for ban",
        delete_messages="Delete messages from last N days (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided",
        delete_messages: Optional[int] = 0
    ):
        """Ban a member from the server"""
        
        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't ban yourself!", ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message("❌ You can't ban bots!", ephemeral=True)
            return
        
        if member.id == interaction.guild.owner_id:
            await interaction.response.send_message("❌ You can't ban the server owner!", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You can't ban someone with a higher or equal role!", ephemeral=True)
            return
        
        if delete_messages < 0 or delete_messages > 7:
            await interaction.response.send_message("❌ Delete messages days must be between 0-7!", ephemeral=True)
            return
        
        try:
            await member.ban(reason=f"{reason} | By: {interaction.user}", delete_message_days=delete_messages)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned from the server",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Messages Deleted", value=f"Last {delete_messages} days", inline=True)
            
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this member!", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server (Mod only)")
    @app_commands.describe(
        user_id="User ID to unban",
        reason="Reason for unban"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self, 
        interaction: discord.Interaction, 
        user_id: str,
        reason: Optional[str] = "No reason provided"
    ):
        """Unban a user from the server"""
        
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID!", ephemeral=True)
            return
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found!", ephemeral=True)
            return
        
        try:
            await interaction.guild.unban(user, reason=f"{reason} | By: {interaction.user}")
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{user.mention} has been unbanned",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message("❌ This user is not banned!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unban users!", ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a member (Mod only)")
    @app_commands.describe(
        member="Member to warn",
        reason="Reason for warning"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        """Warn a member (sends them a DM)"""
        
        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't warn yourself!", ephemeral=True)
            return
        
        if member.bot:
            await interaction.response.send_message("❌ You can't warn bots!", ephemeral=True)
            return
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title="⚠️ Warning",
                description=f"You have been warned in **{interaction.guild.name}**",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=False)
            
            await member.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False
        
        # Confirm in channel
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="DM Sent", value="✅ Yes" if dm_sent else "❌ No (DMs closed)", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="purge", description="Delete multiple messages (Mod only)")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(
        self, 
        interaction: discord.Interaction, 
        amount: int
    ):
        """Bulk delete messages from the channel"""
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"✅ Deleted {len(deleted)} message(s)!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages!", ephemeral=True)
    
    # Error handlers
    @timeout.error
    @untimeout.error
    @kick.error
    @ban.error
    @unban.error
    @warn.error
    @purge.error
    async def mod_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
