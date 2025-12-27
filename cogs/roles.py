import discord
from discord import app_commands
from discord.ext import commands
import json
import os

ROLES_DATA_FILE = "roles_data.json"

def load_roles_data():
    if os.path.exists(ROLES_DATA_FILE):
        try:
            with open(ROLES_DATA_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
        except json.JSONDecodeError:
            print("⚠️ Warning: roles_data.json is corrupted, creating new file")
            return {}
    return {}

def save_roles_data(data):
    with open(ROLES_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

roles_data = load_roles_data()

class SelfRoleView(discord.ui.View):
    def __init__(self, guild_id: int, category: str):
        super().__init__(timeout=None)
        self.guild_id = str(guild_id)
        self.category = category
        
        if self.guild_id in roles_data and self.category in roles_data[self.guild_id]:
            role_list = roles_data[self.guild_id][self.category]
            for role_info in role_list:
                button = discord.ui.Button(
                    label=role_info['name'],
                    style=discord.ButtonStyle.primary,
                    custom_id=f"selfrole:{self.guild_id}:{self.category}:{role_info['id']}"
                )
                button.callback = self.button_callback
                self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data['custom_id']
        _, guild_id, category, role_id = custom_id.split(":")
        role_id = int(role_id)
        
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            return
        
        member = interaction.user
        
        if guild_id in roles_data and category in roles_data[guild_id]:
            category_role_ids = [r['id'] for r in roles_data[guild_id][category]]
            roles_to_remove = [r for r in member.roles if r.id in category_role_ids]
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
            
            if role in member.roles:
                await interaction.response.send_message(
                    f"✅ Removed role: **{role.name}**", 
                    ephemeral=True
                )
            else:
                await member.add_roles(role)
                await interaction.response.send_message(
                    f"✅ Added role: **{role.name}**\n(Removed other {category} roles)", 
                    ephemeral=True
                )

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Re-register persistent views
        for guild_id, categories in roles_data.items():
            for category in categories.keys():
                view = SelfRoleView(guild_id=int(guild_id), category=category)
                self.bot.add_view(view)
        print(f"✅ Loaded persistent views for {len(roles_data)} guild(s)")
    
    @app_commands.command(name="role-create", description="Create a self-assignable role (Admin only)")
    @app_commands.describe(
        category="Category for this role (e.g., gaming, color, hobbies)",
        rolename="Name of the role to create"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def role_create(self, interaction: discord.Interaction, category: str, rolename: str):
        guild = interaction.guild
        category = category.lower()
        
        if category in ["color", "colour"]:
            bot_top_role = guild.me.top_role
            position = bot_top_role.position - 1
            color_value = discord.Color.random()
        else:
            position = 1
            color_value = discord.Color.default()
        
        try:
            new_role = await guild.create_role(
                name=rolename,
                permissions=discord.Permissions.none(),
                color=color_value,
                hoist=False,
                mentionable=False
            )
            
            await new_role.edit(position=position)
            
            guild_id = str(guild.id)
            if guild_id not in roles_data:
                roles_data[guild_id] = {}
            
            if category not in roles_data[guild_id]:
                roles_data[guild_id][category] = []
            
            role_exists = any(r['id'] == new_role.id for r in roles_data[guild_id][category])
            if not role_exists:
                roles_data[guild_id][category].append({
                    'id': new_role.id,
                    'name': rolename
                })
                save_roles_data(roles_data)
            
            await interaction.response.send_message(
                f"✅ Created role **{rolename}** in category **{category}**\n"
                f"Role ID: {new_role.id}\n"
                f"Position: {'Top (for colors)' if category in ['color', 'colour'] else 'Standard'}",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to create roles!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating role: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="role-display", description="Display self-role buttons (Admin only)")
    @app_commands.describe(category="Category to display")
    @app_commands.checks.has_permissions(administrator=True)
    async def role_display(self, interaction: discord.Interaction, category: str):
        guild_id = str(interaction.guild.id)
        category = category.lower()
        
        if guild_id not in roles_data or category not in roles_data[guild_id]:
            await interaction.response.send_message(
                f"❌ No roles found in category **{category}**!",
                ephemeral=True
            )
            return
        
        role_list = roles_data[guild_id][category]
        
        if not role_list:
            await interaction.response.send_message(f"❌ Category **{category}** is empty!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎭 {category.capitalize()} Roles",
            description=f"Click the buttons below to get or remove **{category}** roles!",
            color=discord.Color.blurple()
        )
        
        role_names = [f"• {role['name']}" for role in role_list]
        embed.add_field(name="Available Roles:", value="\n".join(role_names), inline=False)
        embed.set_footer(text="Click a button to toggle a role • Only one role per category!")
        
        view = SelfRoleView(guild_id=int(guild_id), category=category)
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send(f"✅ Self-role panel for **{category}** created!", ephemeral=True)
    
    @app_commands.command(name="role-list", description="List all self-role categories")
    async def role_list(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in roles_data or not roles_data[guild_id]:
            await interaction.response.send_message("❌ No self-roles configured yet!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 Self-Role Categories",
            description="Here are all available self-role categories:",
            color=discord.Color.green()
        )
        
        for category, role_list in roles_data[guild_id].items():
            role_names = [role['name'] for role in role_list]
            embed.add_field(
                name=f"🏷️ {category.capitalize()}",
                value="\n".join([f"• {name}" for name in role_names]) if role_names else "No roles",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="role-delete", description="Delete a role (Admin only)")
    @app_commands.describe(category="Category name", rolename="Role to delete")
    @app_commands.checks.has_permissions(administrator=True)
    async def role_delete(self, interaction: discord.Interaction, category: str, rolename: str):
        guild_id = str(interaction.guild.id)
        category = category.lower()
        
        if guild_id not in roles_data or category not in roles_data[guild_id]:
            await interaction.response.send_message(f"❌ Category **{category}** not found!", ephemeral=True)
            return
        
        role_list = roles_data[guild_id][category]
        role_to_delete = None
        
        for role_info in role_list:
            if role_info['name'].lower() == rolename.lower():
                role_to_delete = role_info
                break
        
        if not role_to_delete:
            await interaction.response.send_message(f"❌ Role **{rolename}** not found!", ephemeral=True)
            return
        
        role = interaction.guild.get_role(role_to_delete['id'])
        if role:
            try:
                await role.delete()
            except:
                pass
        
        role_list.remove(role_to_delete)
        
        if not role_list:
            del roles_data[guild_id][category]
        
        save_roles_data(roles_data)
        await interaction.response.send_message(f"✅ Deleted role **{rolename}**", ephemeral=True)
    
    @role_create.error
    @role_display.error
    @role_delete.error
    async def role_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Roles(bot))
