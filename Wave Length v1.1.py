## _       _____ _    ________   __    _______   ________________  __ 
##| |     / /   | |  / / ____/  / /   / ____/ | / / ____/_  __/ / / / 
##| | /| / / /| | | / / __/    / /   / __/ /  |/ / / __  / / / /_/ /  
##| |/ |/ / ___ | |/ / /___   / /___/ /___/ /|  / /_/ / / / / __  /   
##|__/|__/_/  |_|___/_____/  /_____/_____/_/ |_/\____/ /_/ /_/ /_/    
##                                                                V1.1

# https://discord.com/api/oauth2/authorize?client_id=1113643537918087228&permissions=2147493888&scope=bot

# v1.1 is the official release
# Added message for every ten incorrect tries
# Silented all non-important messages to reduce spam


import random
import json
import asyncio
import time
import discord
from discord import app_commands
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())
listOfGames = {}
thoughtLock = asyncio.Lock()

class GamesActive:
    def __init__(self, serverID, channelID):
        self.serverID = serverID
        self.channelID = channelID
        self.currentPlayers = {}
        self.activePlayers = []
        self.thoughtsHad = []
        self.thoughtsCheck = []
        self.thoughtsBanned = []
        self.numberOfPlayers = 2
        self.readyPlayers = 0
        self.rememberMessage = None


def check_game(interaction):
    if interaction.channel.id not in listOfGames:
        listOfGames[interaction.channel.id] = GamesActive(interaction.guild.id, interaction.channel.id)
    return listOfGames[interaction.channel.id]


@bot.event
async def on_ready():
    print("Bot is ready")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    if not wipe.is_running():
        await bot.wait_until_ready()
        wipe.start()


@bot.tree.command(name="think", description = "Give a word or phrase.")
@app_commands.describe(thought = "What do you want to think?")
async def have_thought(interaction: discord.Interaction, thought: str):
    async with thoughtLock:
        currentGame = check_game(interaction)
            
        if thought.lower().replace(" ","") in currentGame.thoughtsBanned:
            await interaction.response.send_message(f"{thought} has already been thought of. Think another thought.", ephemeral=True)
        elif (interaction.user.id not in currentGame.activePlayers) and (len(currentGame.activePlayers) == currentGame.numberOfPlayers):
            print(interaction.user.id, currentGame.activePlayers)
            await interaction.response.send_message("Maximum number of brains connected. Adjust number of participants with /wlplayercount or wait for the next round of calibration.", ephemeral=True)
        elif interaction.user.id not in currentGame.currentPlayers:
            await interaction.response.send_message(f"You're thinking {thought}...", ephemeral=True)

            currentGame.currentPlayers[interaction.user.id] = thought
            currentGame.activePlayers.append(interaction.user.id)

            currentGame.thoughtsHad.append(thought)
            currentGame.thoughtsCheck.append(thought.lower().replace(" ",""))
            currentGame.readyPlayers += 1

            if len(currentGame.currentPlayers) <= currentGame.numberOfPlayers:
                if currentGame.rememberMessage is None:
                    currentGame.rememberMessage = (await interaction.channel.send(embed = discord.Embed(title = "Thoughts collected", description = ("[" + ":brain:"*currentGame.readyPlayers) + (":record_button:"*(currentGame.numberOfPlayers-currentGame.readyPlayers)) + "]")))
                else:
                    await currentGame.rememberMessage.edit(embed = discord.Embed(title = "Thoughts collected", description = ("[" + ":brain:"*currentGame.readyPlayers) + (":record_button:"*(currentGame.numberOfPlayers-currentGame.readyPlayers)) + "]"))
            
            if (len(currentGame.currentPlayers) == currentGame.numberOfPlayers) and (len(currentGame.thoughtsHad) == currentGame.numberOfPlayers):
                await compare_thoughts(interaction)
                    
        else:
            await interaction.response.send_message(f"You're already thinking \"{currentGame.currentPlayers[interaction.user.id]}.\" You can't change your mind, wait for the others to have a thought.", ephemeral=True)

       

@bot.tree.command(name="wlhelp", description="Explain how to play.")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("Participants each think of a word or phrase using the /think command. Once each participant has a thought, all thoughts are shown. If all thoughts are the same word or phrase, the mind linking process will become successful. The goal is to find a word or phrase in common with all thoughts given until all participants arrive to the same thought.\n\nFor example, if one player says \"House\" and another says \"Knight\" the next thought they each think should relate to \"House\" and \"Knight\" somehow, like \"Castle\" or \"Stable.\"\n\nTo adjust the number of participants, use /wlplayercount. To reset the test, use /wlclear.", ephemeral=True)


@bot.tree.command(name="wlclear", description="Restart linking process.")
async def clear(interaction: discord.Interaction):
    await interaction.response.send_message("Restarting linking progress.", ephemeral=True)
    currentGame = check_game(interaction)
    currentGame.currentPlayers.clear()
    currentGame.thoughtsHad.clear()
    currentGame.thoughtsCheck.clear()
    currentGame.thoughtsBanned.clear()
    currentGame.rememberMessage = None
    currentGame.readyPlayers = 0
    del listOfGames[interaction.channel.id]
    await interaction.channel.send(embed = discord.Embed(description = f"{interaction.user.global_name} has restarted the linking process.", silent=True))


@bot.tree.command(name="wlplayercount", description = "Change number of currentPlayers.")
@app_commands.describe(number = "How many currentPlayers?")
async def player_count(interaction: discord.Interaction, number: int):
    currentGame = check_game(interaction)

    if 2 <= number <= 100:
        currentGame.numberOfPlayers = number
        await interaction.response.send_message("Player count adjusted.", ephemeral=True)
        await interaction.channel.send(embed = discord.Embed(description = f"Now linking {number} brains."), silent = True)
        if len(currentGame.currentPlayers) == currentGame.numberOfPlayers:
            await compare_thoughts(interaction)
    elif number < 2:
        await interaction.response.send_message("Player count cannot go below two. We have already established a link with your brain.", ephemeral=True)
    elif number > 100:
        await interaction.response.send_message("Player count cannot go above human population (100).", ephemeral=True)


async def compare_thoughts(interaction):
    currentGame = check_game(interaction)
        
    await interaction.channel.send(embed = discord.Embed(title = "You all thought:", description = " :small_blue_diamond: ".join(currentGame.thoughtsHad)))
    
    if all(thoughts == currentGame.thoughtsCheck[0] for thoughts in currentGame.thoughtsCheck):
        await interaction.channel.send(content="# :arrow_right::brain::arrow_up: LINK ACHIEVED :arrow_up::brain::arrow_left:\n### THANK YOU FOR YOUR PARTICIPATION.", silent=True)
        del listOfGames[interaction.channel.id]
    else:
        await interaction.channel.send(embed = discord.Embed(description = ":x: Link Not Established. Try Again. :x:"), silent=True)
        currentGame.currentPlayers.clear()
        currentGame.thoughtsBanned.extend(currentGame.thoughtsCheck)
        currentGame.thoughtsHad.clear()
        currentGame.thoughtsCheck.clear()
        currentGame.readyPlayers = 0
        currentGame.rememberMessage = None  
        if len(currentGame.thoughtsBanned) % 30 == 0:
            await interaction.channel.send(embed = discord.Embed(description = random.choice(("Mental mismatch detected. Administering electrical recalibration... Success. Resuming connection attempt.",\
                                                                                             "Neural incompatibility detected. Spinal fluid transfusion initialized... Success. Resuming connection attempt.",\
                                                                                             "Cerebral discordance detected. Initialzing genomic revision... Success. Resuming connection attempt."))), silent=True)
@tasks.loop(hours=168)
async def wipe():
    listOfGames.clear()
    print("All Games Reset")


with open("AUTH_TOKEN.txt", "r") as auth:
    bot.run(auth.read())
