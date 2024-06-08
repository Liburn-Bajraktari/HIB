import subprocess
import discord
from discord.ext import commands, tasks
import os
import logging
import asyncio

# Setup logging
logging.basicConfig(filename='AudioBot_Py.log', level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Create Intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot
bot_token = 'Token Goes Here'  # Discord Token
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store the log channel ID for each guild
log_channel_ids = {}

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
        await voice_client.guild.me.edit(deafen=True)
    else:
        voice_client = ctx.voice_client
        if voice_client.channel != channel:
            await voice_client.move_to(channel)
            await voice_client.guild.me.edit(deafen=True)

    # Run the Node.js script to download audio
    process = subprocess.run(['node', 'download.js', search_term])
    if process.returncode != 0:
        await ctx.send(f"Failed to download or play '{search_term}'. Please try a different song or command")
    else:
        # Add both the search term and context to the queue
        queue.append((search_term, ctx))
        logging.info(f"Added {search_term} to queue")


@tasks.loop(seconds=1)
async def process_queue():
    global queue

    for guild in bot.guilds:
        voice_client = guild.voice_client

        if voice_client and not voice_client.is_playing() and queue:
            # Get the next search term from the queue
            search_term, ctx = queue.pop(0)
            # Wait until the filename.txt file exists, up to a maximum of 5 attempts
            filename_path = 'downloads\\filename.txt'
            for i in range(5):
                if os.path.exists(filename_path):
                    break
                await asyncio.sleep(1)
            else:
                print(f"Failed to find filename for {search_term}")
                return

            # Read the filename from the filename.txt file
            with open(filename_path, 'r') as file:  # Corrected path
                filename = file.read().strip()

            # Remove the .mp3 extension
            display_name = os.path.basename(filename)[:-4]

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


@bot.command(brief="This will set a default channel to send the messages to", aliases=['ch', 'channel'])
@commands.has_permissions(administrator=True)  # Restrict to admins
# Set the Default channel
async def set_log_channel(ctx, channel: discord.TextChannel):
    log_channel_ids[ctx.guild.id] = channel.id
    await ctx.send(f"Log channel set to {channel.mention}")


# Function to send a message to the log channel
# Not Fully Utilized yet
async def send_to_log_channel(guild, message):
    channel_id = log_channel_ids.get(guild.id)
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(message)
        else:
            print(f"Channel with ID {channel_id} not found")
    else:
        print("Log channel not set for this guild")


@bot.event
async def on_ready():
    process_queue.start()

    for guild in bot.guilds:
        # Set the log channel ID to the first text channel of the guild
        log_channel_ids[guild.id] = next(
            (channel.id for channel in guild.text_channels), None)


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and not after.deaf:
        # Deafen the bot again
        await member.guild.me.edit(deafen=True)
        await send_to_log_channel(member.guild,
                                  "To maintain stability of the bot, we need the bot to stay deafened... "
                                  "or whatever the other bots said, idk")


def run_bot():
    bot.run(bot_token)  # Use environment variable for token


if __name__ == '__main__':
    run_bot()
