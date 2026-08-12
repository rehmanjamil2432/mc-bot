import os
import asyncio
import time
import discord
from discord.ext import tasks, commands
from mcstatus import JavaServer

# --- CONFIGURATION ---
SERVER_IP = "play.flashhuh.net"

# ⚠️ Yahan apni Discord Channel ki ID paste kar dena
NOTIFICATION_CHANNEL_ID = 1536291987647631370  

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# State Tracking Variables
was_online = None          
offline_start_time = None  

@bot.event
async def on_ready():
    print(f"✅ Notification Bot is now online as: {bot.user.name}")
    check_server_status.start()

@tasks.loop(seconds=30)  # Checks every 30 seconds
async def check_server_status():
    global was_online, offline_start_time

    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        print("⚠️ Channel ID invalid or bot lacks permissions.")
        return

    is_currently_online = False
    online_players = 0
    max_players = 0
    ping = 0

    # 1. Ping Minecraft Java Server
    try:
        server = await JavaServer.async_lookup(SERVER_IP)
        status = await server.async_status()
        is_currently_online = True
        online_players = status.players.online
        max_players = status.players.max
        ping = round(status.latency)
    except Exception:
        is_currently_online = False

    current_time = time.time()

    if was_online is None:
        was_online = is_currently_online
        if not is_currently_online:
            offline_start_time = current_time
        return

    # --- SCENARIO 1: SERVER STOPPED / OFFLINE ---
    if was_online and not is_currently_online:
        was_online = False
        offline_start_time = current_time

        embed = discord.Embed(
            title="🚨 SERVER OFFLINE / STOPPED",
            description=(
                "**The server is currently unreachable or has been stopped.**\n"
                "Players have been disconnected. The system will continue monitoring "
                "and send an update as soon as the server boots back up!"
            ),
            color=discord.Color.red()
        )
        embed.add_field(name="🌐 Server IP", value=f"`{SERVER_IP}`", inline=True)
        embed.add_field(name="📊 Status", value="🔴 Offline", inline=True)
        embed.set_footer(text="Flash Network • Server Status Alert")
        await channel.send(embed=embed)

    # --- SCENARIO 2: SERVER BACK ONLINE / RESTARTED ---
    elif not was_online and is_currently_online:
        was_online = True
        offline_duration = current_time - (offline_start_time or current_time)

        # RESTART ALERT (Offline for 3 minutes or less)
        if offline_duration <= 180:
            embed = discord.Embed(
                title="🔄 SERVER RESTARTED SUCCESSFULLY",
                description=(
                    "**The server maintenance/restart cycle has completed successfully!**\n"
                    "All services have been reloaded. You can now rejoin the game and continue playing."
                ),
                color=discord.Color.gold()
            )
            embed.add_field(name="🌐 Server IP", value=f"`{SERVER_IP}`", inline=False)
            embed.add_field(name="👥 Online Players", value=f"**{online_players} / {max_players}**", inline=True)
            embed.add_field(name="📶 Latency", value=f"{ping} ms", inline=True)
            embed.add_field(name="⏱️ Downtime", value=f"{int(offline_duration)}s", inline=True)
            embed.set_footer(text="Flash Network • Server Reboot Detected")
            await channel.send(embed=embed)

        # ONLINE ALERT (Offline for longer than 3 minutes)
        else:
            embed = discord.Embed(
                title="🟢 SERVER IS NOW ONLINE",
                description=(
                    "**Great news! The server is back up and open for everyone.**\n"
                    "Grab your gear, invite your friends, and jump right into the game!"
                ),
                color=discord.Color.green()
            )
            embed.add_field(name="🌐 Server IP", value=f"`{SERVER_IP}`", inline=False)
            embed.add_field(name="👥 Online Players", value=f"**{online_players} / {max_players}**", inline=True)
            embed.add_field(name="📶 Latency", value=f"{ping} ms", inline=True)
            embed.set_footer(text="Flash Network • Online Status Alert")
            await channel.send(embed=embed)

        offline_start_time = None

    # Update Bot Activity Status
    if is_currently_online:
        await bot.change_presence(
            activity=discord.Game(name=f"🎮 {online_players}/{max_players} Online | play.flashhuh.net")
        )
    else:
        await bot.change_presence(
            activity=discord.Game(name="🔴 Server Offline")
        )

# Run Bot
token = "MTUzNzAzNzgwNDM0MzY1NjUyMA.GylohG.d0hB65iS0LCUgogDtd3Ky4jpNegaOJEIGUTyGs"
if token:
    bot.run(token)
else:
    print("⚠️ DISCORD_TOKEN missing!")
