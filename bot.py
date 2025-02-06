import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
import logging
from ai_handler import init_guessing_game, next_hint

logging.basicConfig(level=logging.DEBUG)
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

@bot.slash_command(name="add", guild_ids=[TESTING_GUILD_ID])
async def add(interaction: nextcord.Interaction, left: int, right: int):
    """Adds two numbers together."""
    await interaction.response.send_message(left + right)

@bot.slash_command(name="start", guild_ids=[TESTING_GUILD_ID])
async def start(interaction: nextcord.Interaction):
    await interaction.response.defer()
    # await interaction.followup.send("Starting game...")
    game = init_guessing_game()
    game["attempts"] = 0
    game["word"] = game["word"].lower()
    # print(f"game: {game}")
    game_sessions[interaction.guild.id] = game
    await interaction.followup.send("""Welcome to my little guessing game! Try and guess the word I am thinking of.
             Go ahead an take a shot in the dark, and I will give you hints if you get
             it wrong. Guess by typing '!guess' followed by your guess.""")
    
@bot.slash_command(name="guess", guild_ids=[TESTING_GUILD_ID])
async def guess(interaction: nextcord.Interaction, guess: str):
    await interaction.response.defer()
    # await interaction.followup.send("Thinking...")
    session = game_sessions[interaction.guild.id]

    if not session:
        await interaction.followup.send("You haven't started a game yet! Type '!start' to begin!")
        return
    
    correct_word = session["word"]

    if guess.lower() == correct_word:
        await interaction.followup.send(f"{interaction.user.name}! {session["success_message"]}")
        await interaction.followup.send(f"Game Summary: It took you {session["attempts"]} tries to guess the word {session["word"]}")
        del game_sessions[interaction.guild.id]
    else:
        await interaction.followup.send(f"{interaction.user.name} guessed {guess}. Wrong guess! Here's a hint: {session["hints"][-1]}")
        session["attempts"] = int(session["attempts"])
        session["attempts"] += 1
        hint = next_hint(session["attempts"], session["word"], session["hints"], guess)
        session["hints"].append(hint)

bot.run(TOKEN)
