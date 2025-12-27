import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import math
from datetime import datetime, timedelta
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import requests

LEVELS_DATA_FILE = "levels_data.json"
SETTINGS_DATA_FILE = "level_settings.json"
BACKGROUND_IMAGE = r"C:\Users\yosoy\OneDrive\Desktop\Kirito crib\Flowy\leaderboard.jpg"

class Leveling(commands.Cog):
    """Complete XP and Leveling System like MEE6"""
    
    def __init__(self, bot):
        self.bot = bot
        self.levels_data = self.load_levels_data()
        self.settings = self.load_settings()
        self.cooldowns = {}
        
    def load_levels_data(self):
        """Load user level data from JSON"""
        if os.path.exists(LEVELS_DATA_FILE):
            try:
                with open(LEVELS_DATA_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ levels_data.json corrupted, creating new")
                return {}
        return {}
    
    def save_levels_data(self):
        """Save user level data to JSON"""
        with open(LEVELS_DATA_FILE, 'w') as f:
            json.dump(self.levels_data, f, indent=4)
    
    def load_settings(self):
        """Load leveling settings from JSON"""
        if os.path.exists(SETTINGS_DATA_FILE):
            try:
                with open(SETTINGS_DATA_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ level_settings.json corrupted, creating new")
                return {}
        return {}
    
    def save_settings(self):
        """Save leveling settings to JSON"""
        with open(SETTINGS_DATA_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def get_guild_settings(self, guild_id: int):
        """Get settings for a specific guild"""
        guild_id = str(guild_id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {
                "enabled": True,
                "xp_rate": 1.0,
                "xp_min": 15,
                "xp_max": 25,
                "cooldown": 60,
                "level_up_channel": None,
                "level_up_message": "🎉 {user} leveled up to **Level {level}**!",
                "ignored_channels": [],
                "ignored_roles": [],
                "role_rewards": {}
            }
            self.save_settings()
        return self.settings[guild_id]
    
    def get_user_data(self, guild_id: int, user_id: int):
        """Get user XP and level data"""
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}
        
        if user_id not in self.levels_data[guild_id]:
            self.levels_data[guild_id][user_id] = {
                "xp": 0,
                "level": 1,
                "total_xp": 0,
                "messages": 0
            }
            self.save_levels_data()
        
        return self.levels_data[guild_id][user_id]
    
    def calculate_level(self, xp: int) -> int:
        """Calculate level from XP (MEE6 formula)"""
        level = int((-50 + math.sqrt(max(0, 2500 + 20 * xp - 400))) / 10)
        return max(1, level)
    
    def xp_for_level(self, level: int) -> int:
        """Calculate XP needed for a specific level"""
        return 5 * (level ** 2) + (50 * level) + 100
    
    async def fetch_avatar(self, user: discord.Member, size: int = 128):
        """Download and return user avatar as PIL Image"""
        try:
            avatar_url = user.display_avatar.url
            response = requests.get(avatar_url, timeout=5)
            avatar = Image.open(io.BytesIO(response.content)).convert('RGBA')
            avatar = avatar.resize((size, size), Image.Resampling.LANCZOS)
            
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            
            output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            output.paste(avatar, (0, 0))
            output.putalpha(mask)
            
            return output
        except:
            img = Image.new('RGBA', (size, size), (128, 128, 128, 255))
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            img.putalpha(mask)
            return img
    
    async def generate_leaderboard_image(self, guild: discord.Guild, page: int = 1):
        """Generate leaderboard image"""
        guild_data = self.levels_data.get(str(guild.id), {})
        
        if not guild_data:
            return None
        
        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: x[1]["total_xp"],
            reverse=True
        )
        
        per_page = 10
        max_pages = math.ceil(len(sorted_users) / per_page)
        page = max(1, min(page, max_pages))
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = sorted_users[start_idx:end_idx]
        
        width = 800
        header_height = 80
        row_height = 80
        height = header_height + (len(page_users) * row_height) + 30
        
        # Create solid dark base
        img = Image.new('RGB', (width, height), '#0f1014')
        
        # Load background VERY subtle (only 15% visible)
        try:
            if os.path.exists(BACKGROUND_IMAGE):
                bg = Image.open(BACKGROUND_IMAGE).convert('RGB')
                bg = bg.resize((width, height), Image.Resampling.LANCZOS)
                # Apply heavy blur for aesthetic
                bg = bg.filter(ImageFilter.GaussianBlur(radius=3))
                # Only 15% opacity - VERY subtle
                img = Image.blend(img, bg, 0.15)
        except Exception as e:
            print(f"Background load error: {e}")
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 38)
            name_font = ImageFont.truetype("arialbd.ttf", 24)
            stats_font = ImageFont.truetype("arial.ttf", 17)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            stats_font = ImageFont.load_default()
        
        # Header with slight transparency
        draw.rectangle([(0, 0), (width, header_height)], fill=(20, 22, 26))
        
        title_text = "🏆 Leaderboard"
        try:
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
        except:
            title_width = len(title_text) * 19
        
        draw.text(((width - title_width) // 2, 15), title_text, fill='#FFD700', font=title_font)
        
        page_text = f"Page {page}/{max_pages}"
        try:
            page_bbox = draw.textbbox((0, 0), page_text, font=stats_font)
            page_width = page_bbox[2] - page_bbox[0]
        except:
            page_width = len(page_text) * 9
        
        draw.text(((width - page_width) // 2, 56), page_text, fill='#72767d', font=stats_font)
        
        y_offset = header_height + 12
        
        for idx, (user_id, data) in enumerate(page_users, start=start_idx + 1):
            member = guild.get_member(int(user_id))
            if not member:
                continue
            
            row_y = y_offset + ((idx - start_idx - 1) * row_height)
            
            # Much darker rows with better contrast
            if idx % 2 == 0:
                row_bg = (18, 20, 24)
            else:
                row_bg = (22, 24, 28)
            
            # Draw row with rounded corners
            draw.rounded_rectangle([(12, row_y), (width - 12, row_y + row_height - 8)], 
                                radius=8, fill=row_bg, outline='#2f3136', width=2)
            
            # Rank
            if idx == 1:
                rank_text = "🥇"
                rank_color = '#FFD700'
            elif idx == 2:
                rank_text = "🥈"
                rank_color = '#C0C0C0'
            elif idx == 3:
                rank_text = "🥉"
                rank_color = '#CD7F32'
            else:
                rank_text = f"#{idx}"
                rank_color = '#72767d'
            
            draw.text((28, row_y + 24), rank_text, fill=rank_color, font=name_font)
            
            # Avatar
            avatar = await self.fetch_avatar(member, size=52)
            img.paste(avatar, (85, row_y + 14), avatar)
            
            # Username
            username = member.display_name[:17]
            draw.text((150, row_y + 12), username, fill='#FFFFFF', font=name_font)
            
            # Stats
            level_text = f"Lvl {data['level']}"
            xp_text = f"{data['total_xp']:,} XP"
            
            draw.text((150, row_y + 42), level_text, fill='#5865f2', font=stats_font)
            draw.text((250, row_y + 42), xp_text, fill='#3ba55d', font=stats_font)
            
            # Progress bar
            bar_x = 470
            bar_y = row_y + 24
            bar_width = 290
            bar_height = 24
            
            current_level = data['level']
            current_xp = data['total_xp']
            xp_for_current = self.xp_for_level(current_level)
            xp_for_next = self.xp_for_level(current_level + 1)
            xp_progress = max(0, current_xp - xp_for_current)
            xp_needed = max(1, xp_for_next - xp_for_current)
            progress = min(max(xp_progress / xp_needed, 0), 1.0)
            
            # Progress background
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], 
                                radius=12, fill='#0f1014', outline='#2f3136', width=1)
            
            # Progress fill with gradient effect
            if progress > 0:
                fill_width = max(int(bar_width * progress), 24)
                # Create gradient by drawing multiple rectangles
                for i in range(fill_width):
                    alpha = 1.0 - (i / fill_width) * 0.2
                    r = int(88 * alpha)
                    g = int(101 * alpha)
                    b = int(242 * alpha)
                    draw.rectangle([(bar_x + i, bar_y + 1), (bar_x + i + 1, bar_y + bar_height - 1)], 
                                fill=(r, g, b))
                
                # Round the fill
                draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height)], 
                                    radius=12, outline=None)
            
            # Progress text
            progress_text = f"{int(progress * 100)}%"
            try:
                progress_bbox = draw.textbbox((0, 0), progress_text, font=stats_font)
                progress_width = progress_bbox[2] - progress_bbox[0]
            except:
                progress_width = len(progress_text) * 8
            
            draw.text((bar_x + (bar_width - progress_width) // 2, bar_y + 5), 
                    progress_text, fill='#FFFFFF', font=stats_font)
        
        output = io.BytesIO()
        img.save(output, format='PNG', quality=98)
        output.seek(0)
        
        return output

    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP on message"""
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        guild_id = message.guild.id
        user_id = message.author.id
        
        settings = self.get_guild_settings(guild_id)
        
        if not settings["enabled"]:
            return
        
        if message.channel.id in settings["ignored_channels"]:
            return
        
        user_role_ids = [role.id for role in message.author.roles]
        if any(role_id in settings["ignored_roles"] for role_id in user_role_ids):
            return
        
        cooldown_key = f"{guild_id}:{user_id}"
        current_time = datetime.now()
        
        if cooldown_key in self.cooldowns:
            last_time = self.cooldowns[cooldown_key]
            if (current_time - last_time).total_seconds() < settings["cooldown"]:
                return
        
        self.cooldowns[cooldown_key] = current_time
        
        user_data = self.get_user_data(guild_id, user_id)
        
        base_xp = random.randint(settings["xp_min"], settings["xp_max"])
        xp_gain = int(base_xp * settings["xp_rate"])
        
        old_level = user_data["level"]
        user_data["xp"] += xp_gain
        user_data["total_xp"] = max(0, user_data["total_xp"] + xp_gain)
        user_data["messages"] += 1
        
        new_level = self.calculate_level(user_data["total_xp"])
        user_data["level"] = new_level
        
        self.save_levels_data()
        
        if new_level > old_level:
            await self.handle_level_up(message, new_level, settings)
    
    async def handle_level_up(self, message, new_level, settings):
        """Handle level up event"""
        level_up_msg = settings["level_up_message"].format(
            user=message.author.mention,
            level=new_level,
            server=message.guild.name
        )
        
        if settings["level_up_channel"]:
            channel = message.guild.get_channel(settings["level_up_channel"])
            if channel:
                await channel.send(level_up_msg)
            else:
                await message.channel.send(level_up_msg)
        else:
            await message.channel.send(level_up_msg)
        
        if str(new_level) in settings["role_rewards"]:
            role_id = settings["role_rewards"][str(new_level)]
            role = message.guild.get_role(role_id)
            if role:
                try:
                    await message.author.add_roles(role)
                    await message.channel.send(f"🎁 {message.author.mention} earned the **{role.name}** role!")
                except discord.Forbidden:
                    pass
    
    @app_commands.command(name="rank", description="Check your or someone's rank and level")
    @app_commands.describe(member="Member to check (leave empty for yourself)")
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Show user's rank card"""
        target = member or interaction.user
        
        if target.bot:
            await interaction.response.send_message("❌ Bots don't have levels!", ephemeral=True)
            return
        
        user_data = self.get_user_data(interaction.guild.id, target.id)
        
        guild_data = self.levels_data.get(str(interaction.guild.id), {})
        sorted_users = sorted(
            guild_data.items(),
            key=lambda x: x[1]["total_xp"],
            reverse=True
        )
        
        rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == str(target.id)), 0)
        
        current_level = user_data["level"]
        current_xp = max(0, user_data["total_xp"])
        xp_for_current = self.xp_for_level(current_level)
        xp_for_next = self.xp_for_level(current_level + 1)
        xp_progress = max(0, current_xp - xp_for_current)
        xp_needed = max(1, xp_for_next - xp_for_current)
        
        embed = discord.Embed(
            title=f"📊 Rank Card - {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Rank", value=f"#{rank}", inline=True)
        embed.add_field(name="⭐ Level", value=f"{current_level}", inline=True)
        embed.add_field(name="💬 Messages", value=f"{user_data['messages']}", inline=True)
        
        progress_pct = min(max(xp_progress / xp_needed, 0), 1.0)
        embed.add_field(
            name="📈 XP Progress",
            value=f"{xp_progress}/{xp_needed} XP\n`[{'█' * int(progress_pct * 10)}{'░' * (10 - int(progress_pct * 10))}]`",
            inline=False
        )
        embed.add_field(name="💎 Total XP", value=f"{current_xp:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="View server XP leaderboard")
    @app_commands.describe(page="Page number (default: 1)")
    async def leaderboard(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Show XP leaderboard with image"""
        await interaction.response.defer()
        
        guild_data = self.levels_data.get(str(interaction.guild.id), {})
        
        if not guild_data:
            await interaction.followup.send("❌ No one has earned XP yet!", ephemeral=True)
            return
        
        image_bytes = await self.generate_leaderboard_image(interaction.guild, page)
        
        if image_bytes is None:
            await interaction.followup.send("❌ Failed to generate leaderboard!", ephemeral=True)
            return
        
        file = discord.File(image_bytes, filename="leaderboard.png")
        await interaction.followup.send(file=file)
    
    @app_commands.command(name="xp-add", description="Add XP to a user (Admin only)")
    @app_commands.describe(member="Member to give XP", amount="Amount of XP to add")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.bot:
            await interaction.response.send_message("❌ Can't give XP to bots!", ephemeral=True)
            return
        
        user_data = self.get_user_data(interaction.guild.id, member.id)
        old_level = user_data["level"]
        
        user_data["xp"] += amount
        user_data["total_xp"] = max(0, user_data["total_xp"] + amount)
        
        new_level = self.calculate_level(user_data["total_xp"])
        user_data["level"] = new_level
        
        self.save_levels_data()
        
        embed = discord.Embed(title="✅ XP Added", description=f"Added **{amount} XP** to {member.mention}", color=discord.Color.green())
        embed.add_field(name="Total XP", value=f"{user_data['total_xp']:,}", inline=True)
        embed.add_field(name="Level", value=f"{old_level} → {new_level}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="xp-remove", description="Remove XP from a user (Admin only)")
    @app_commands.describe(member="Member to remove XP from", amount="Amount of XP to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_remove(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.bot:
            await interaction.response.send_message("❌ Bots don't have XP!", ephemeral=True)
            return
        
        user_data = self.get_user_data(interaction.guild.id, member.id)
        old_level = user_data["level"]
        
        user_data["xp"] = max(0, user_data["xp"] - amount)
        user_data["total_xp"] = max(0, user_data["total_xp"] - amount)
        
        new_level = self.calculate_level(user_data["total_xp"])
        user_data["level"] = new_level
        
        self.save_levels_data()
        
        embed = discord.Embed(title="✅ XP Removed", description=f"Removed **{amount} XP** from {member.mention}", color=discord.Color.orange())
        embed.add_field(name="Total XP", value=f"{user_data['total_xp']:,}", inline=True)
        embed.add_field(name="Level", value=f"{old_level} → {new_level}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="xp-set", description="Set user's XP (Admin only)")
    @app_commands.describe(member="Member to set XP", amount="XP amount to set")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_set(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.bot:
            await interaction.response.send_message("❌ Can't set XP for bots!", ephemeral=True)
            return
        
        user_data = self.get_user_data(interaction.guild.id, member.id)
        
        user_data["xp"] = amount
        user_data["total_xp"] = max(0, amount)
        user_data["level"] = self.calculate_level(user_data["total_xp"])
        
        self.save_levels_data()
        
        await interaction.response.send_message(
            f"✅ Set {member.mention}'s XP to **{amount:,}** (Level {user_data['level']})"
        )
    
    @app_commands.command(name="xp-reset", description="Reset user's XP and level (Admin only)")
    @app_commands.describe(member="Member to reset")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_reset(self, interaction: discord.Interaction, member: discord.Member):
        if member.bot:
            await interaction.response.send_message("❌ Bots don't have XP!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.levels_data and user_id in self.levels_data[guild_id]:
            del self.levels_data[guild_id][user_id]
            self.save_levels_data()
        
        await interaction.response.send_message(f"✅ Reset {member.mention}'s XP and level")
    
    @app_commands.command(name="xp-config", description="Configure XP settings (Admin only)")
    @app_commands.describe(
        xp_rate="XP multiplier (e.g., 1.5 = 50% more XP)",
        xp_min="Minimum XP per message",
        xp_max="Maximum XP per message",
        cooldown="Cooldown between XP gains (seconds)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_config(
        self,
        interaction: discord.Interaction,
        xp_rate: Optional[float] = None,
        xp_min: Optional[int] = None,
        xp_max: Optional[int] = None,
        cooldown: Optional[int] = None
    ):
        settings = self.get_guild_settings(interaction.guild.id)
        
        if xp_rate is not None:
            settings["xp_rate"] = max(0.1, min(10.0, xp_rate))
        if xp_min is not None:
            settings["xp_min"] = max(1, xp_min)
        if xp_max is not None:
            settings["xp_max"] = max(settings["xp_min"], xp_max)
        if cooldown is not None:
            settings["cooldown"] = max(0, cooldown)
        
        self.save_settings()
        
        embed = discord.Embed(title="⚙️ XP Configuration", color=discord.Color.blue())
        embed.add_field(name="XP Rate", value=f"{settings['xp_rate']}x", inline=True)
        embed.add_field(name="XP Range", value=f"{settings['xp_min']}-{settings['xp_max']}", inline=True)
        embed.add_field(name="Cooldown", value=f"{settings['cooldown']}s", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="xp-toggle", description="Enable/disable XP system (Admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_toggle(self, interaction: discord.Interaction):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["enabled"] = not settings["enabled"]
        self.save_settings()
        
        status = "✅ Enabled" if settings["enabled"] else "❌ Disabled"
        await interaction.response.send_message(f"{status} XP system")
    
    @app_commands.command(name="xp-ignore-channel", description="Ignore channel for XP (Admin only)")
    @app_commands.describe(channel="Channel to ignore")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        settings = self.get_guild_settings(interaction.guild.id)
        
        if channel.id in settings["ignored_channels"]:
            settings["ignored_channels"].remove(channel.id)
            await interaction.response.send_message(f"✅ {channel.mention} will now earn XP")
        else:
            settings["ignored_channels"].append(channel.id)
            await interaction.response.send_message(f"❌ {channel.mention} will no longer earn XP")
        
        self.save_settings()
    
    @app_commands.command(name="xp-role-reward", description="Set role reward for level (Admin only)")
    @app_commands.describe(level="Level to award role at", role="Role to award")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_role_reward(self, interaction: discord.Interaction, level: int, role: discord.Role):
        settings = self.get_guild_settings(interaction.guild.id)
        settings["role_rewards"][str(level)] = role.id
        self.save_settings()
        
        await interaction.response.send_message(f"✅ Set {role.mention} as reward for reaching Level {level}")
    
    @xp_add.error
    @xp_remove.error
    @xp_set.error
    @xp_reset.error
    @xp_config.error
    @xp_toggle.error
    @xp_ignore_channel.error
    @xp_role_reward.error
    async def xp_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Leveling(bot))
