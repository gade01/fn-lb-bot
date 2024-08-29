import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
import os
import shutil

# Intents allow the bot to access server member information
intents = discord.Intents.default()
intents.members = True  # Enable the privileged members intent
intents.message_content = True  # Enable if you need to process message content
intents.messages = True

# Initialize the bot with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Directly set the Fortnite Tracker API key
FORTNITE_API_KEY = "YOUR_FORTNITE_API_KEY"

# Default data structure
default_data = {
    "daily": {},
    "weekly": {},
    "season": {},
    "lifetime": {},
    "channels": {}
}

# Define role IDs
ROLE_IDS = {
    "daily": {
        "top_10": "1234567890",
        "top_3": "1234567890",
        "top_2": "1234567890",
        "top_1": "1234567890"
    },
    "weekly": {
        "top_10": "1234567890",
        "top_3": "1234567890",
        "top_2": "1234567890",
        "top_1": "1234567890"
    },
    "season": {
        "top_10": "1234567890",
        "top_3": "1234567890",
        "top_2": "1234567890",
        "top_1": "1234567890"
    },
    "lifetime": {
        "top_10": "1234567890",
        "top_3": "1234567890",
        "top_2": "1234567890",
        "top_1": "1234567890"
    }
}

def load_user_data():
    if not os.path.exists('user_fortnite_data.json'):
        print("File not found. Creating a new file.")
        save_user_data(default_data)
        return default_data

    try:
        with open('user_fortnite_data.json', 'r') as f:
            data = json.load(f)
            print("Data loaded successfully.")
            return data
    except json.JSONDecodeError:
        print("JSON decoding error. Creating a new file.")
        save_user_data(default_data)
        return default_data

def load_backup_data():
    if not os.path.exists('user_fortnite_data_backup.json'):
        print("Backup file not found.")
        return default_data

    try:
        with open('user_fortnite_data_backup.json', 'r') as f:
            data = json.load(f)
            print("Backup data loaded successfully.")
            return data
    except json.JSONDecodeError:
        print("JSON decoding error with backup file.")
        return default_data

def backup_user_data():
    if os.path.exists('user_fortnite_data.json'):
        shutil.copy('user_fortnite_data.json', 'user_fortnite_data_backup.json')
        print("Backup created successfully.")

def save_user_data(data):
    try:
        # Create a backup before saving
        backup_user_data()

        with open('user_fortnite_data.json', 'w') as f:
            json.dump(data, f, indent=4)
            print("Data saved successfully.")
    except Exception as e:
        print(f"Failed to save data: {e}")

def merge_data(old_data, new_data):
    merged_data = old_data.copy()

    for period in ["daily", "weekly", "season", "lifetime"]:
        if period in new_data:
            for user_id, user_info in new_data[period].items():
                if user_id in merged_data[period]:
                    # Update existing user
                    merged_data[period][user_id].update(user_info)
                else:
                    # Add new user
                    merged_data[period][user_id] = user_info

    return merged_data

def remove_user(user_id):
    data = load_user_data()

    for period in ["daily", "weekly", "season", "lifetime"]:
        if user_id in data[period]:
            del data[period][user_id]

    save_user_data(data)
    print(f"User ID '{user_id}' removed from all leaderboards.")

# Load user data into a global variable
user_fortnite_usernames = load_user_data()

@bot.event
async def on_ready():
    global user_fortnite_usernames
    user_fortnite_usernames = load_user_data()
    print(f"Bot is ready. Logged in as {bot.user}")
    # Start daily task to update leaderboards
    bot.loop.create_task(daily_leaderboard_update())

@bot.command(name="setfortnite")
async def set_fortnite_username(ctx, mentioned_user: discord.Member, *, username: str):
    # Get the ID of the mentioned user
    user_id = str(mentioned_user.id)
    print(f"Setting Fortnite username '{username}' for user ID '{user_id}'")  # Debug

    # Load current data
    current_data = load_user_data()

    # Load old data from backup
    backup_data = load_backup_data()

    # Merge old data with current data
    merged_data = merge_data(backup_data, current_data)

    # Update the data for each period
    for period in ["daily", "weekly", "season", "lifetime"]:
        if user_id in merged_data[period]:
            print(f"Updating existing user ID '{user_id}' in {period} leaderboard.")
        else:
            print(f"Adding new user ID '{user_id}' to {period} leaderboard.")
        
        # Update the data
        merged_data[period][user_id] = {
            "username": username,
            "stats": {}
        }

    # Save merged data to file
    save_user_data(merged_data)
    await ctx.send(f"Fortnite username set to '**{username}**' for <@{mentioned_user.id}>.")

@bot.command(name="removefortnite")
@commands.has_permissions(administrator=True)
async def remove_fortnite_username(ctx, mentioned_user: discord.Member):
    user_id = str(mentioned_user.id)
    remove_user(user_id)
    await ctx.send(f"Removed Fortnite data for <@{mentioned_user.id}>.")

async def get_fortnite_stats(username):
    url = f"https://api.fortnitetracker.com/v1/profile/{username}"
    headers = {
        'TRN-Api-Key': FORTNITE_API_KEY
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Failed to fetch stats for {username}: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Client error while fetching stats for {username}: {e}")
        return None

@bot.command(name="leaderboard")
async def leaderboard(ctx, period: str):
    if period not in ["daily", "weekly", "season", "lifetime"]:
        await ctx.send("Invalid period. Choose from: daily, weekly, season, lifetime.")
        return
    
    leaderboard = []
    for user_id, user_info in user_fortnite_usernames[period].items():
        member = ctx.guild.get_member(int(user_id))
        if member:
            stats = user_info.get("stats", {})
            leaderboard.append({
                "member": member,
                "username": user_info["username"],
                "wins": stats.get("wins", 0),
                "eliminations": stats.get("eliminations", 0),
                "assists": stats.get("assists", 0),
                "damage": stats.get("damage", 0),
                "level": stats.get("level", 0),
                "rank_br": stats.get("br_rank", "N/A"),  # Rank BR
                "rank_zb": stats.get("zb_rank", "N/A")   # Rank ZB
            })

    # Sort leaderboard
    leaderboard.sort(key=lambda x: (x["wins"], x["eliminations"], x["assists"], x["damage"], x["level"]), reverse=True)
    
    # Only keep the top 10 entries
    leaderboard = leaderboard[:10]

    embed = discord.Embed(title=f"Fortnite {period.capitalize()} Leaderboard", color=int("ffc7fa", 16))
    for i, entry in enumerate(leaderboard, 1):
        embed.add_field(
            name=f"{i}. {entry['member'].display_name} ({entry['username']})",
            value=(
                f"Wins: {entry['wins']}\n"
                f"Eliminations: {entry['eliminations']}\n"
                f"Assists: {entry['assists']}\n"
                f"Damage: {entry['damage']}\n"
                f"Level: {entry['level']}\n"
                f"Rank BR: {entry['rank_br']}\n"
                f"Rank ZB: {entry['rank_zb']}"
            ),
            inline=False
        )
    
    await ctx.send(embed=embed)

async def update_roles(guild, period, top_users):
    role_ids = ROLE_IDS.get(period, {})
    roles = {
        "top_10": role_ids.get("top_10"),
        "top_3": role_ids.get("top_3"),
        "top_2": role_ids.get("top_2"),
        "top_1": role_ids.get("top_1")
    }

    for role_name, role_id in roles.items():
        if not role_id:
            continue
        role = discord.utils.get(guild.roles, id=int(role_id))
        if not role:
            print(f"Role '{role_name}' not found for {period} leaderboard.")
            continue

        # Remove role from all members
        for member in guild.members:
            if role in member.roles:
                await member.remove_roles(role)

    # Assign roles to top users
    for i, user_id in enumerate(top_users):
        member = guild.get_member(int(user_id))
        if not member:
            continue
        if i == 0 and roles.get("top_1"):
            await member.add_roles(discord.utils.get(guild.roles, id=int(roles["top_1"])))
        if i < 2 and roles.get("top_2"):
            await member.add_roles(discord.utils.get(guild.roles, id=int(roles["top_2"])))
        if i < 3 and roles.get("top_3"):
            await member.add_roles(discord.utils.get(guild.roles, id=int(roles["top_3"])))
        if i < 10 and roles.get("top_10"):
            await member.add_roles(discord.utils.get(guild.roles, id=int(roles["top_10"])))

async def post_leaderboard_message(channel_id, period):
    channel = bot.get_channel(int(channel_id))
    if not channel:
        print(f"Channel with ID {channel_id} not found.")
        return
    
    # Generate leaderboard data
    leaderboard = []
    for user_id, user_info in user_fortnite_usernames[period].items():
        member = channel.guild.get_member(int(user_id))
        if member:
            stats = user_info.get("stats", {})
            leaderboard.append({
                "member": member,
                "username": user_info["username"],
                "wins": stats.get("wins", 0),
                "eliminations": stats.get("eliminations", 0),
                "assists": stats.get("assists", 0),
                "damage": stats.get("damage", 0),
                "level": stats.get("level", 0),
                "rank_br": stats.get("br_rank", "N/A"),  # Rank BR
                "rank_zb": stats.get("zb_rank", "N/A")   # Rank ZB
            })

    # Sort leaderboard
    leaderboard.sort(key=lambda x: (x["wins"], x["eliminations"], x["assists"], x["damage"], x["level"]), reverse=True)
    
    # Only keep the top 10 entries
    top_10 = leaderboard[:10]
    
    embed = discord.Embed(title=f"Fortnite {period.capitalize()} Leaderboard", color=int("ffc7fa", 16))
    for i, entry in enumerate(top_10, 1):
        embed.add_field(
            name=f"{i}. {entry['member'].display_name} ({entry['username']})",
            value=(
                f"Wins: {entry['wins']}\n"
                f"Eliminations: {entry['eliminations']}\n"
                f"Assists: {entry['assists']}\n"
                f"Damage: {entry['damage']}\n"
                f"Level: {entry['level']}\n"
                f"Rank BR: {entry['rank_br']}\n"
                f"Rank ZB: {entry['rank_zb']}"
            ),
            inline=False
        )
    
    # Check for existing leaderboard message
    async for message in channel.history(limit=100):
        if message.author.id == bot.user.id and message.embeds:
            for embed in message.embeds:
                if embed.title == f"Fortnite {period.capitalize()} Leaderboard":
                    await message.edit(embed=embed)
                    break
            else:
                continue
            break
    else:
        await channel.send(embed=embed)

    # Update roles for the top 10 users
    await update_roles(channel.guild, period, [entry["member"].id for entry in top_10])

async def daily_leaderboard_update():
    while True:
        for period in ["daily", "weekly", "season", "lifetime"]:
            channel_id = user_fortnite_usernames["channels"].get(period)
            if channel_id:
                await post_leaderboard_message(channel_id, period)
        await asyncio.sleep(86400)  # Sleep for 24 hours

@bot.command(name="setleaderboardchannel")
@commands.has_permissions(administrator=True)
async def set_leaderboard_channel(ctx, period: str):
    if period not in ["daily", "weekly", "season", "lifetime"]:
        await ctx.send("Invalid period. Choose from: daily, weekly, season, lifetime.")
        return
    
    user_fortnite_usernames["channels"][period] = str(ctx.channel.id)
    save_user_data(user_fortnite_usernames)
    await ctx.send(f"Leaderboard channel set for {period} leaderboard.")

# Command to get Battle Royale Rank (Rank BR) for a user
@bot.command(name="rank_br")
async def rank_br(ctx, mentioned_user: discord.Member):
    user_id = str(mentioned_user.id)
    season_data = user_fortnite_usernames.get("season", {})

    # Check if user exists in the season leaderboard
    if user_id not in season_data:
        await ctx.send(f"No season data found for <@{mentioned_user.id}>.")
        return

    user_info = season_data[user_id]
    rank_br = user_info["stats"].get("br_rank", "N/A")
    await ctx.send(f"<@{mentioned_user.id}>'s Rank BR: **{rank_br}**")

# Command to get Zero Build Rank (Rank ZB) for a user
@bot.command(name="rank_zb")
async def rank_zb(ctx, mentioned_user: discord.Member):
    user_id = str(mentioned_user.id)
    season_data = user_fortnite_usernames.get("season", {})

    # Check if user exists in the season leaderboard
    if user_id not in season_data:
        await ctx.send(f"Ingen sæson data fundet for <@{mentioned_user.id}>.")
        return

    user_info = season_data[user_id]
    rank_zb = user_info["stats"].get("zb_rank", "N/A")
    await ctx.send(f"<@{mentioned_user.id}>'s Rank ZB: **{rank_zb}**")

# Run the bot with your Discord bot token
bot.run("YOUR_DISCORD_BOT_TOKEN")  # Replace with your actual bot token
