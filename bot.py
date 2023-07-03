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


@bot.tree.command(name = "singles")
@app_commands.describe(player1="Name of player 1",
                       player2="Name of player 2",
                       score1="Score of player 1",
                       score2="Score of player 2")
async def add1v1Game(interaction: discord.Interaction, player1: str, player2: str, score1: int, score2: int):
    lb = loadLb()
    try:
        telemetry = lb.add1pGame(player1, player2, score1, score2)
        saveLb(lb)
        
        await interaction.response.send_message(embed=make1v1Embed(interaction, telemetry))
    except:
        await interaction.response.send_message(f"An error occurred.")

@bot.tree.command(name = "doubles")
@app_commands.describe(p1 = "Name of player 1", 
                       p2 = "Name of player 2", 
                       p3 = "Name of player 3", 
                       p4 = "Name of player 4", 
                       score1 = "Score of team 1", 
                       score2 = "Score of team 2")
async def add2v2Game(interaction: discord.Interaction, p1: str, p2: str, p3: str, p4: str, score1: int, score2: int):
    lb = loadLb()
    # NEED TO CHECK IF PLAYERS EXIST FIRST
    try:
        telemetry = lb.add2pGame(p1, p2, p3, p4, score1, score2)
        saveLb(lb)
        await interaction.response.send_message(embed=make2v2Embed(interaction, telemetry))
    except:
        await interaction.response.send_message(f"An error occurred.")


@bot.tree.command(name = "addplayer")
@app_commands.describe(name = "Name of new player")
async def addPlayer(interaction: discord.Interaction, name: str):
    lb = loadLb()
    if lb.addPlayer(name):
        saveLb(lb)
        print(f"Added new player {name} to leaderboard")
        await interaction.response.send_message(embed=makeNewPlayerEmbed(interaction, name))
    else:
        print(f"Attempted to add new player but \"{name}\" already exists.")
        await interaction.response.send_message(f":exclamation: Attempted to add new player but \"{name}\" already exists. :exclamation:")


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
    # print("Leaderboard requested:")
    # lb = loadLb()
    # string = lb.getPlayers()
    # if len(string) == 0:
    #     print("Leaderboard file is empty.")
    #     await interaction.response.send_message("Leaderboard file is empty.")
    # else:
    #     print(string)
    #     await interaction.response.send_message(string)
    print("Leaderboard requested:")
    lb = loadLb()
    board = lb.getLeaderboard()
    if len(board) == 0:
        print("Leaderboard file is empty.")
        await interaction.response.send_message("Leaderboard file is empty.")
    else:
        await interaction.response.send_message(embed=makeLeaderboardEmbed(interaction, board))


def makeLeaderboardEmbed(interaction: discord.Interaction, board):
    embed = discord.Embed(
        title=f"Leaderboard",
        description=f"{interaction.user.display_name} requested the current leaderboard."
    )
    # make column of names
    namestr = ""
    elostr = ""
    for count, pair in enumerate(board):
        namestr += pair[1] + "\n"
        elostr += f"{pair[0]:.2f}" + "\n"
    embed.add_field(name="Player", value=namestr, inline=True)
    embed.add_field(name="Elo rating", value=elostr, inline=True)
    return embed

def makeNewPlayerEmbed(interaction, name):
    embed = discord.Embed(
        title=f"New Player: {name}",
        description=f"New player \"{name}\" added by {interaction.user.display_name} and initialized to 1500 elo.",
    )
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="ELO", value=1500, inline=True)
    return embed

def make1v1Embed(interaction, telemetry):
    names = telemetry["names"]
    embed = discord.Embed(
            title=f"{interaction.user.display_name} has registered a new match.",
            description=f"**{names[0]}**  *vs.* **{names[1]}**"
        )
    embed.add_field(name="Score", value=f"{telemetry['score'][0]} - {telemetry['score'][1]}", inline=True)
    embed.add_field(name="Avg. Elo", value=telemetry['avgElo'], inline=True)
    embed.add_field(name="Upset/Score Mult.", value=f"{telemetry['upsetMult']}/{telemetry['scoreDeltaMult']}", inline=True)
    #compose player list, old elo, new elo
    names = ""
    oldElo = ""
    newElo = ""
    for i in range(len(telemetry["names"])):
        names += "**" + telemetry["names"][i] + f"** *({telemetry['eloDelta'][i]})*\n"
        oldElo += telemetry["oldElo"][i] + "\n"
        newElo += "→ **" + telemetry["newElo"][i] + "**\n"
    embed.add_field(name="Player", value=names, inline=True)
    embed.add_field(name="Old Elo", value=oldElo, inline=True)
    embed.add_field(name="New Elo", value=newElo, inline=True)
    return embed


def make2v2Embed(interaction, telemetry):
    names = telemetry["names"]
    embed = discord.Embed(
        title=f"{interaction.user.display_name} has registered a new match.",
        description=f"**{names[0]}** *and* **{names[1]}**  *vs.* **{names[2]}** *and* **{names[3]}**"
    )
    embed.add_field(name="Score", value=f"{telemetry['score'][0]} - {telemetry['score'][1]}", inline=True)
    embed.add_field(name="Avg. Elo", value=telemetry['avgElo'], inline=True)
    embed.add_field(name="Upset/Score Mult.", value=f"{telemetry['upsetMult']}/{telemetry['scoreDeltaMult']}", inline=True)
    #compose player list, old elo, new elo
    names = ""
    oldElo = ""
    newElo = ""
    for i in range(len(telemetry["names"])):
        names += "**" + telemetry["names"][i] + f"** *({telemetry['eloDelta'][i]})*\n"
        oldElo += telemetry["oldElo"][i] + "\n"
        newElo += "→ **" + telemetry["newElo"][i] + "**\n"

    embed.add_field(name="Player", value=names, inline=True)
    embed.add_field(name="Old Elo", value=oldElo, inline=True)
    embed.add_field(name="New Elo", value=newElo, inline=True)
    return embed



with open('token.key') as f:
    token = f.readline()

bot.run(token)





    