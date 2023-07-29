import subprocess
import discord
from discord.ext import commands
import time
import os
import logging
import asyncio

# Setup logging
logging.basicConfig(filename='AudioBot_Py_Log.log', level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Create Intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Create a queue of search terms
queue = []

@bot.command(brief="This will play a song", aliases=['p', 'pla'])
async def play(ctx, *, search_term: str):
    global queue

    logging.info(f"Received play command with search term: {search_term}")

    if ctx.author.voice is None:
        await ctx.send("You're not connected to a voice channel!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    logging.info(f"Voice client after connect or move: {voice_client}")


    # Add the search term to the queue
    queue.append(search_term)
    logging.info(f"Added {search_term} to queue")

    # If the bot is not currently playing audio, start processing the queue
    if not voice_client.is_playing() and not voice_client.is_paused():
        await process_queue(ctx, voice_client)

async def process_queue(ctx, voice_client):
    global queue

    while queue:
        # Get the next search term from the queue
        search_term = queue.pop(0)
        filename = f"{search_term.replace(' ', '_')}.mp3"

        # Run the Node.js script to download audio
        subprocess.run(['node', 'download.js', search_term, filename])

        # Wait until the file exists, up to a maximum of 5 attempts
        for i in range(5):
            if os.path.exists(filename):
                break
            time.sleep(5)
        else:
            await ctx.send(f"Failed to download audio for {search_term}")
            return

        # Play the downloaded audio file
        audio_source = discord.FFmpegPCMAudio(filename)
        voice_client.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)

        # Wait for the audio to finish playing before processing the next item in the queue
        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(1)

@bot.command(brief="This will display the current queue", aliases=['q', 'que'])
async def display_queue(ctx):
    global queue

    # Display the current queue
    await ctx.send('\n'.join(queue))

bot.run('MTEzNDU5MzAyMjcwNTgxNTY4Nw.GEIEbP.19Eu0de_uR8TDROED6mEDe8gr__93DGNgJQeFA')
