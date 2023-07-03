import discord
from discord import app_commands
from discord.ext import commands
from Leaderboard import Leaderboard
import pickle
import os

#=========================================================================================================

def loadLb():
    if os.path.exists(os.getcwd()+"/lb.pickle"):
        with open("lb.pickle", "rb") as f:
            lb = pickle.load(f)
        print("Leaderboard found and loaded.")
    else:
        lb = Leaderboard()
        print("Leaderboard file DNE, created new.")
    return lb

def saveLb(lb):
    with open("lb.pickle", "wb") as f:
        pickle.dump(lb, f)
    print("Leaderboard saved.")

#=========================================================================================================

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot is up and ready, creating or loading leaderboard object...")
    lb = loadLb()
    saveLb(lb)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name = "2v2game")
@app_commands.describe(p1 = "Name of player 1", 
                       p2 = "Name of player 2", 
                       p3 = "Name of player 3", 
                       p4 = "Name of player 4", 
                       score1 = "Score of team 1", 
                       score2 = "Score of team 2")
async def add2pGame(interaction: discord.Interaction, p1: str, p2: str, p3: str, p4: str, score1: int, score2: int):
    lb = loadLb()
    # NEED TO CHECK IF PLAYERS EXIST FIRST
    try:
        string = lb.add2pGame(p1, p2, p3, p4, score1, score2, report=True)
        print(string)
        saveLb(lb)
        await interaction.response.send_message(string)
    except:
        await interaction.response.send_message(f"An error occurred.")

@bot.tree.command(name = "addplayer")
@app_commands.describe(name = "Name of new player")
async def addPlayer(interaction: discord.Interaction, name: str):
    lb = loadLb()
    lb.addPlayer(name)
    lb.getPlayers()
    saveLb(lb)
    print(f"Added new player {name} to leaderboard")
    await interaction.response.send_message(f"Added new player {name}")

@bot.tree.command(name="setelo")
@app_commands.describe(name = "Name of player to adjust", elo = "Elo value to set")
async def setElo(interaction: discord.Interaction, name: str, elo: int):
    lb = loadLb()
    if lb.setElo(name, elo):
        saveLb(lb)
        await interaction.response.send_message(f"Set {name} elo to {elo}.")
    else: 
        await interaction.response.send_message(f"That person doesn't exist.")

@bot.tree.command(name="leaderboard")
async def getLb(interaction: discord.Interaction):
    print("Leaderboard requested:")
    lb = loadLb()
    string = lb.getPlayers()
    if len(string) == 0:
        print("Leaderboard file is empty.")
        await interaction.response.send_message("Leaderboard file is empty.")
    else:
        print(string)
        await interaction.response.send_message(string)


with open('token.key') as f:
    token = f.readline()

bot.run(token)





    