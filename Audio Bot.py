import subprocess
import discord
from discord.ext import commands, tasks
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

    # Add a delay to prevent overloading
    await asyncio.sleep(5)  # Async delay for 5 seconds

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

    # Add both the search term and context to the queue
    queue.append((search_term, ctx))
    logging.info(f"Added {search_term} to queue")

    # Run the Node.js script to download audio
    subprocess.run(['node', 'download.js', search_term])


@tasks.loop(seconds=1)
async def process_queue():
    global queue

    for guild in bot.guilds:
        voice_client = guild.voice_client

        if voice_client and not voice_client.is_playing() and queue:
            # Get the next search term from the queue
            search_term, ctx = queue.pop(0)
            # Wait until the filename.txt file exists, up to a maximum of 5 attempts
            for i in range(5):
                if os.path.exists('filename.txt'):
                    break
                time.sleep(1)
            else:
                print(f"Failed to find filename for {search_term}")
                return

            # Read the filename from the filename.txt file
            with open('filename.txt', 'r') as file:
                filename = file.read().strip()

            # Remove the .mp3 extension
            display_name = filename[:-4]

            # Play the downloaded audio file
            def after_playing(error):
                if error:
                    print(f'Player error: {error}')
                else:
                    if os.path.exists(filename):
                        try:
                            os.remove(filename)
                            print(f'Successfully deleted file {filename}')
                        except Exception as e:
                            print(f'Failed to delete file {filename}: {e}')
                    else:
                        print(f'Warning: File {filename} not found, skipping deletion.')

            voice_client.play(discord.FFmpegPCMAudio(filename), after=after_playing)

            await ctx.send('Now Playing **' + display_name + '**')


@bot.command(brief="This will display the current queue", aliases=['q', 'queue'])
async def display_queue(ctx):
    global queue

    # Inform user if queue is empty
    if not queue:
        await ctx.send("Queue is empty!")
        return

    # Display the current queue
    enumerated_queue = [f"{idx + 1}. {item}" for idx, item in enumerate(queue)]
    await ctx.send('\n'.join(enumerated_queue))


@bot.event
async def on_ready():
    process_queue.start()


def run_bot():
    bot.run('Your Discord Token')


if __name__ == '__main__':
    run_bot()
