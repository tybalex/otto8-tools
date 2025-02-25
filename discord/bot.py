import discord
import sys
from discord import app_commands
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def get_channels():
    for guild in client.guilds:  # Loop through all servers the bot is in
        print(f"Server: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:  # Get text channels
            print(f"  - Channel: {channel.name} (ID: {channel.id})")

    await client.close()  # Stop the bot after retrieving channel info




async def _get_channel_safe(client, channel_id):
    channel = client.get_channel(channel_id)  # Try cache first
    if channel is None:
        try:
            channel = await client.fetch_channel(channel_id)  # Fetch if not found
        except discord.NotFound:
            print("Error: Channel not found!")
        except discord.Forbidden:
            print("Error: Bot lacks permissions!")
        except discord.HTTPException as e:
            print(f"Error: {e}")
    return channel

async def send_message():
    CHANNEL_ID = "1343451835888963615"
    try:
        channel = await _get_channel_safe(client, CHANNEL_ID)  # Fetch instead of get_channel
        print(f"Channel found: {channel.name}")
        response = await channel.send("Hello, Discord YBPark! 🎉")
        print(f"Message sent: {response.id}")
        
    except discord.NotFound:
        print("Error: Channel not found!")
    except discord.Forbidden:
        print("Error: Bot lacks permissions to access the channel!")
    except discord.HTTPException as e:
        print(f"Error: {e}")
    await client.close() 



GUILD_ID = "1343451744822099998"
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # await tree.sync(guild=discord.Object(id=GUILD_ID))
    await get_channels()
    
    # await send_message()  # Calling the custom function
    
# @client.event
# async def on_message(message):
#     # Ignore messages sent by the bot itself
#     if message.author == client.user:
#         return

#     print(f"Message from {message.author}: {message.content}")

#     # Example: If someone says "hello", the bot replies
#     if message.content.lower() == "hello":
#         await message.channel.send(f"Hello, {message.author.name}!")


@tree.command(name="hello", description="Say hello to the bot!", guild=discord.Object(id=GUILD_ID))
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.name}! 👋")


user_threads = {}

@tree.command(name="chat", description="Start a thread and reply inside it.", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message="The message to start the thread with")
async def thread_command(interaction: discord.Interaction, message: str):
    if isinstance(interaction.channel, discord.Thread):  # If used inside a thread
        await interaction.response.send_message(f"{interaction.user.mention}, I'm continuing in this thread! You said: {message}")
    else:  # If used in a normal text channel, create a new thread
        thread = await interaction.channel.create_thread(
            name=f"{interaction.user.name}'s Thread",
            type=discord.ChannelType.public_thread,
            auto_archive_duration=60
        )
        await thread.send(f"{interaction.user.mention} started this thread: {message}")
        await interaction.response.send_message(f"Thread created! Join here: {thread.jump_url}", ephemeral=True)



# Bot Listens for Messages in Threads It Created
@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Ignore bot's own messages

    if isinstance(message.channel, discord.Thread):  # Ensure the message is inside a thread
        thread = message.channel

        try:
            # Fetch the actual thread starter message
            if thread.owner_id:
                print(f"Thread owner ID: {thread.owner_id}")
                if thread.owner_id == client.user.id:
                    await thread.send(f"{message.author.mention}, I'm here to help! You said: {message.content}")
        except discord.NotFound:
            pass  # If the thread's starter message isn't found, do nothing
    
    if message.content.startswith("!history"):
        async for msg in message.channel.history(limit=10):  # No limit (fetches everything)
            print(f"{msg.author}: {msg.content}")
        
        await message.channel.send("Retrieved 10 chat history!")

client.run(TOKEN)
