import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
import logging
from ai_handler import init_guessing_game, next_hint, cheeky_quit

logging.basicConfig(level=logging.INFO)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

description = """An exciting adventure where you collect items and ships."""
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

game_sessions = {}

bot = commands.Bot(description=description, intents=intents)

TESTING_GUILD_ID = int(415928729676808192)
@bot.event
async def on_ready():
    try:
        guilds = [guild async for guild in bot.fetch_guilds(limit=1)]  # Test API request
        print(f"✅ API Connection Successful: Found {len(guilds)} guild(s)")
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
    await bot.sync_all_application_commands(delete_unknown=True)

# @bot.event
# async def on_interaction(interaction: nextcord.Interaction):
#     print(f"📩 Received interaction: {interaction.data}")
#     try:
#         await interaction.response.send_message("✅ Interaction received!", ephemeral=True)
#     except Exception as e:
#         print(f"❌ Interaction failed: {e}")

# @bot.event
# async def on_socket_response(payload):
#     print(f"🌐 Received WebSocket Event: {payload}")

@bot.slash_command(name="test", guild_ids=[TESTING_GUILD_ID])
async def test(interaction: nextcord.Interaction):
    await interaction.response.send_message("Test?")

@bot.slash_command(name="add", description="A command to add two numbers together used for testing.", guild_ids=[TESTING_GUILD_ID])
async def add(interaction: nextcord.Interaction, left: int, right: int):
    """Adds two numbers together."""
    await interaction.response.send_message(left + right)

@bot.slash_command(name="start", description="Start the guessing game.", guild_ids=[TESTING_GUILD_ID])
async def start(interaction: nextcord.Interaction):
    await interaction.response.defer()
    if game_sessions.get(interaction.guild.id):
        del game_sessions[interaction.guild.id]
    game = init_guessing_game()
    game["attempts"] = 0
    game["word"] = game["word"].lower()
    # print(f"game: {game}")
    game_sessions[interaction.guild.id] = game
    await interaction.followup.send("""Welcome to my little guessing game! Try and guess the word I am thinking of.
             Go ahead an take a shot in the dark, and I will give you hints if you get
             it wrong. Take a guess by typing a single word into the chat.""")
    
@bot.slash_command(name="guess", description="Type your one word guess with or without preceeding command: /guess", guild_ids=[TESTING_GUILD_ID])
async def guess(interaction: nextcord.Interaction, guess: str):
    await interaction.response.defer()
    await process_guess(interaction, guess)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not game_sessions.get(message.guild.id):
        return

    words = message.content.strip().split()

    if len(words) == 1:
        await process_guess(message, words[0])
    bot.process_commands(message)    

@bot.slash_command(name="quit", description="Quit the game. The AI will see you out...", guild_ids=[TESTING_GUILD_ID])
async def quit(interaction: nextcord.Interaction):
    await interaction.response.defer()
    session = game_sessions[interaction.guild.id]

    quit_message = cheeky_quit(session["attempts"], session["word"])
    await interaction.followup.send(quit_message)
    del game_sessions[interaction.guild.id]

async def process_guess(target, guess: str):
    # Check if target is an Interaction or a Message
    is_interaction = isinstance(target, nextcord.Interaction)

    # Get the Guild ID
    guild_id = target.guild.id if is_interaction else target.guild.id  # Ensures consistency

    # Get the user object correctly
    user = target.user if is_interaction else target.author  # ✅ FIXED

    session = game_sessions.get(guild_id)

    if not session:
        response = "You haven't started a game yet! Type '/start' to begin!"
    else:
        correct_word = session["word"]

        if guess.lower() == correct_word:
            response = (
                f"{user.name}! {session['success_message']}\n"
                f"Game Summary: It took you {session['attempts']} tries to guess the word '{session['word']}'"
            )
            del game_sessions[guild_id]  # Clear session after a correct guess
        else:
            response = (
                f"{user.name} guessed {guess}. "
                f"Wrong guess! Here's a hint: {session['hints'][-1]}"
            )
            session["attempts"] = int(session["attempts"]) + 1
            hint = next_hint(session["attempts"], session["word"], session["hints"], guess)
            session["hints"].append(hint)

    # Send response correctly based on the context
    if is_interaction:
        await target.followup.send(response)  # ✅ Interaction case
    else:
        await target.channel.send(response)  # ✅ Message case (Use `.channel.send()`)




bot.run(TOKEN)
