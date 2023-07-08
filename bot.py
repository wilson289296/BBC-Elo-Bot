import discord
from discord import app_commands
from discord.ext import commands
from Leaderboard import Leaderboard
import json
import os

#================================================= Generic funcs ========================================================

def loadLb():
    if os.path.exists(os.getcwd()+"/lbdata.json"):
        with open("lbdata.json", "r") as f:
            lbdata = json.load(f)
        lb = Leaderboard()
        lb.loadData(lbdata)
        print("Leaderboard found and loaded.")
    else:
        lb = Leaderboard()
        print("Leaderboard file DNE, created new.")
    return lb

def saveLb(lb):
    lbdata = lb.dumpData()
    with open("lbdata.json", "w") as f:
        json.dump(lbdata, f)
    print("Leaderboard saved.")

def stringSanitation(string): # responds with False if sanitation fails, or responds with sanitized string if succeeds
    # add fail conditions over time, will probably have more
    if len(string) > 25:
        return False
    else:
        return string.lower()

def scoreValidation(score1, score2):
    #bounds checking
    if score1 < 0 or score1 > 30:
        return "Score error: score1 value out of bounds."
    if score2 < 0 or score2 > 30: 
        return "Score error: score2 value out of bounds."
    if score1 < 21 and score2 < 21:
        return "Score error: incomplete game."
    if (score1 >= 22 and score2 <= 19) or (score2 >= 22 and score1 <= 19): #checking for impossible >21
        return "Score error: impossible score."
    # all clear
    return "valid"
    
    

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
    # sanitize input
    player1 = stringSanitation(player1)
    player2 = stringSanitation(player2)
    if not (player1 and player2):
        await interaction.response.send_message(f"Something is wrong with the names provided.")
        return
    result = scoreValidation(score1, score2)
    if result != "valid":
        await interaction.response.send_message(result)
        return
    
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
    p1 = stringSanitation(p1)
    p2 = stringSanitation(p2)
    p3 = stringSanitation(p3)
    p4 = stringSanitation(p4)
    if not (p1 and p2 and p3 and p4):
        await interaction.response.send_message(f"Something is wrong with the names provided.")
        return
    result = scoreValidation(score1, score2)
    if result != "valid":
        await interaction.response.send_message(result)
        return
    
    try:
        telemetry = lb.add2pGame(p1, p2, p3, p4, score1, score2)
        saveLb(lb)
        await interaction.response.send_message(embed=make2v2Embed(interaction, telemetry))
    except:
        await interaction.response.send_message(f"An error occurred.")


@bot.tree.command(name = "addplayer")
@app_commands.describe(name = "Name of new player")
async def addPlayer(interaction: discord.Interaction, name: str):
    name = stringSanitation(name)
    lb = loadLb()
    if lb.addPlayer(name):
        saveLb(lb)
        print(f"Added new player {name} to leaderboard")
        await interaction.response.send_message(embed=makeNewPlayerEmbed(interaction, name))
    else:
        print(f"Attempted to add new player but \"{name}\" already exists.")
        await interaction.response.send_message(f":exclamation: Attempted to add new player but \"{name}\" already exists. :exclamation:")


@bot.tree.command(name="setelo")
@app_commands.describe(name = "Name of player to adjust", elo = "Elo value to set", password = "Admin password")
async def setElo(interaction: discord.Interaction, name: str, elo: int, password: str):
    name = stringSanitation(name)
    with open('pw.key') as f:
        pw = f.readline()
    
    if password == pw:
        lb = loadLb()
        if lb.setElo(name, elo):
            saveLb(lb)
            await interaction.response.send_message(f"Set {name} elo to {elo}.")
        else: 
            await interaction.response.send_message(f"That person doesn't exist.")
    else:
        await interaction.response.send_message(f"Incorrect password.")


@bot.tree.command(name="leaderboard")
async def getLb(interaction: discord.Interaction):
    print("Leaderboard requested:")
    lb = loadLb()
    board = lb.getLeaderboard()
    if len(board) == 0:
        print("Leaderboard file is empty.")
        await interaction.response.send_message("Leaderboard file is empty.")
    else:
        await interaction.response.send_message(embed=makeLeaderboardEmbed(interaction, board))


# ================================= EMBED MAKERS ====================================================


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





    