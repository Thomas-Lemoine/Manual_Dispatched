#Dispatched.py
import cProfile
import discord
import random
from discord.ext import commands,tasks
import os
import asyncio
import json
import time

intents = discord.Intents().all()

client = commands.Bot(command_prefix = ".", intents = intents, activity= discord.Game("Running from the Entity"))

#GLOBAL VARIABLES (TRY TO AVOID!)
ADMINROLENAME = "Host"
client.state = {}
client.rooms = {}
client.items = ["FlameT", "FlameT", "Axe", "Axe", "Axe", "Fuel", "Fuel", "Fuel", "Test", "Rope", "Rope", "Rope", "EngineP", "Mop"]
client.Fuelslist = ["Fuel Barrel", "Fuel Barrel"]
client.Characters = {}
client.Players = {}


@client.event
async def on_ready():
        print("Bot is ready.")

@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')
    logschan = discord.utils.get(member.guild.text_channels, name = "logs")
    if member.bot:
        await logschan.send(f"The bot {member.mention} has joined.")
    else:
        await logschan.send(f"{member.mention} has joined. They will be part of the next game.")

@client.event
async def on_member_remove(member):
    print(f'{member} has left the server {member.guild.name}.')


"""

CLASSES

"""

class Room:
    
    def __init__(self, roomchat, roomitemschannel, roomrole):
        self.name = roomchat.name
        self.roomchat = roomchat
        self.roomitemschannel = roomitemschannel
        self.roomrole = roomrole
        self.items = []
        #Create the blank embed of the items
        self.itemsembed = None
        self.itemsmessage = None
    
    async def additem(self, *itemname):
        itemname = ' '.join(itemname)
        #print(self)
        self.items.append(itemname)
        desc = "\n".join([str(item) for item in self.items])
        self.itemsembed = discord.Embed(title = self.roomrole.name, description = desc)
        await self.itemsmessage.edit(embed = self.itemsembed)
        return True
    
    async def removeitem(self, *itemname):
        itemname = ' '.join(itemname)
        if itemname in self.items:
            self.items.remove(itemname)
            if len(self.items) == 0:
                self.itemsembed = discord.Embed(title = self.roomrole.name, description = "No items")
                await self.itemsmessage.edit(embed = self.itemsembed)
            else:
                desc = "\n".join([str(item) for item in self.items])
                self.itemsembed = discord.Embed(title = self.roomrole.name, description = desc)
                await self.itemsmessage.edit(embed = self.itemsembed)
            return True
        else:
            return False

    async def inititemsmsg(self):
        desc = "No items"
        self.itemsembed = discord.Embed(title = self.roomrole.name, description = desc)
        self.itemsmessage = await self.roomitemschannel.send(embed = self.itemsembed)
        return True
    
    @staticmethod
    async def create(roomchat, roomitemschannel, roomrole):
        x = Room(roomchat, roomitemschannel, roomrole)
        await x.inititemsmsg()
        return x

class Player:

    def __init__(self, membertype):
        self.membertype = membertype
        self.name = self.membertype.name
        self.nickname = self.membertype.display_name

        #Nones
        self.playerchannel = None
        self.Room = None
        self.Roomchannel = None
        self.Roomrole = None
        self.Character = None
        self.Charactername = None
        self.items = []
        self.Characterembed = None
        self.isEntity = False
    
    async def addprivchannel(self, ctx, privatechannel):
        self.playerchannel = privatechannel
        role = await findrole(ctx, self.playerchannel)
        await self.membertype.add_roles(role)
        return True
    
    async def moveroom(self, Room):
        if self.Room != None:
            await self.membertype.remove_roles(self.roomrole)
        self.Room = Room
        self.roomrole = self.Room.roomrole
        self.roomchannel = self.Room.roomchat
        await self.membertype.add_roles(self.roomrole)
        return True

    async def giveEntity(self, entityembed):
        self.isEntity = True
        await self.playerchannel.send(embed = entityembed.set_footer(text = "Do .info Entity for more information about the abilities."))
        return True
    
    async def addChar(self, Character):
        self.Character = Character
        self.Charactername = Character.name
        self.Characterembed = Character.embed
        self.nickname = self.Charactername
        await self.membertype.edit(nick = self.nickname)
        return True
    
    @staticmethod
    async def create(ctx, membertype, privatechannel, Room, Character):
        x = Player(membertype)
        await x.addprivchannel(ctx, privatechannel)
        await x.addChar(Character)
        await x.moveroom(Room)
        DispatchedInfo = await openDispatchedInfojson()
        url = DispatchedInfo["Information"]["map"]
        initializationembed = x.Characterembed.set_footer(text = "Please change your profile picture to the one shown above. Do .info for more information on your Character's abilities and general information about Dispatched.") 
        await x.playerchannel.send(embed = discord.Embed(title = "Outpost").set_image(url = url))
        await asyncio.sleep(0.1)
        x.charembedmsg = await x.playerchannel.send(embed = initializationembed)
        return x

class Character:
    
    def __init__(self, name):
        self.name = name
    
    async def findembed(self):
        DispatchedInfo = await openDispatchedInfojson()
        title = self.name
        image_url = DispatchedInfo["Characters"][self.name]["image_url"]
        self.url = image_url
        Abilitieslst = DispatchedInfo["Characters"][self.name]["Abilities"]
        self.abilities = Abilitieslst
        desc = "\n".join(Abilitieslst)
        self.embed = discord.Embed(title = title, description = desc).set_image(url = image_url)

    @staticmethod
    async def create(name):
        x = Character(name)
        await x.findembed()
        return x



"""

COMMANDS

"""

@client.command(name = "say")
async def _say(ctx, *Messagelst):
    message = " ".join(Messagelst)
    Playertype = await findplayer(ctx)
    await Playertype.Room.roomchat.send(f'*{message}*')
    msg = await ctx.send(f"The following message was successfully carried in {Playertype.Room.roomrole} :\n*{message}*")
    await msg.delete(delay = 5)
    await ctx.message.delete()


@commands.has_role(ADMINROLENAME)
@client.command(name = "a", aliases = ["additem"])
async def _additem(ctx, *args):
    itemname = " ".join(args)
    inplayerchannel = False
    listofextraitems = ["Fuel Barrel", "EFuel"]
    if itemname in client.items or itemname in listofextraitems:
        removeitemfromplayernick = True
    else:
        removeitemfromplayernick = False
    if ctx.channel.name[:3] == "pla":
        Playertype = await findplayer(ctx)
        Roomtype = Playertype.Room
        inplayerchannel = True
    else:
        channel = await findchannel(ctx, ctx.message.channel)
        Roomtype = client.rooms[channel.name][0]
    await ctx.message.delete()
    if await Roomtype.additem(itemname):
        if inplayerchannel:
            msg = await ctx.send(f"The item {itemname} was added to {Roomtype.name}.")
            await msg.delete(delay = 5)
            if removeitemfromplayernick:
                nickname = Playertype.membertype.display_name
                items = nickname.split("(")
                itemslist = []
                for i in range(len(items)):
                    if len(items) == 1:
                        break
                    if i == 0:
                        pass
                    elif items[i][-1] == ")":
                        itemslist.append(items[i][:-1])
                    else:
                        itemslist.append(items[i])
                if itemname in itemslist:
                    itemslist.remove(itemname)
                newnick = items[0]
                for item in itemslist:
                    newnick += f'({item})'
                await Playertype.membertype.edit(nick = newnick)
        return
    await (await ctx.send("You could not add this item for some reason dude.")).delete(delay = 5)

@commands.has_role(ADMINROLENAME)
@client.command(name = "r", aliases = ["removeitem"])
async def _removeitem(ctx, *args):
    itemname = " ".join(args)
    listofextraitems = ["Fuel Barrel", "EFuel"]
    if itemname in client.items or itemname in listofextraitems:
        additemtoplayernick = True
    else:
        additemtoplayernick = False
    inplayerchannel = False
    if ctx.channel.name[:3] == "pla":
        Playertype = await findplayer(ctx)
        Roomtype = Playertype.Room
        inplayerchannel = True
    else:
        channel = await findchannel(ctx, ctx.message.channel)
        Roomtype = client.rooms[channel.name][0]
    await ctx.message.delete()
    if await Roomtype.removeitem(itemname):
        if inplayerchannel:
            if additemtoplayernick:
                await Playertype.membertype.edit(nick = (f'{Playertype.membertype.display_name}({itemname})'))
            msg = await ctx.send(f"The item {itemname} was removed from {Roomtype.name}.")
            await msg.delete(delay = 5)
        return
    await (await ctx.send("This item isn't in the room dude.")).delete(delay = 5)


@commands.has_role(ADMINROLENAME)
@client.command(name = "setup", aliases = ["initialize", "init"])
async def initialization(ctx):
    starttime = time.time()
    #Load DispatchedInfo
    DispatchedInfo = await openDispatchedInfojson()
    
    #Initialize main Embed
    title = "Initializing..."
    desc = "Dispatched is currently beginning the setup."
    thumbnail = DispatchedInfo["Information"]["Dispatched_image"]
    setupembed = discord.Embed(title = title, description = desc).set_image(url = thumbnail)
    
    #Send the embed and save the message so it can be edited easily later on
    setupembedmsg = await ctx.send(embed = setupembed)

    #Removing everyone's roles
    firstdel = time.time()
    await _removeroles(ctx, write_out = False)
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Deleting all member roles...", value = f"Time : {round(time.time() - firstdel,1)} seconds.", inline = False))


    #Deleting and cloning all channels and adding a blank embed for each RoomItems channel.
    #Saves the list of all Room classes, the list of all Channel types for the private channels (in order) and the time this function took to complete.
    roomslst, playerchanlst, timespent = await delall(ctx)
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Recreating all channels...", value = f"Time : {round(timespent,1)} seconds.", inline = False))

    #creating the dictionary for the rooms
    for room in roomslst:
        client.rooms[room.name] = [room,[]]

    #A list of all the room names to be able to easily cycle through and see all their names
    listofroomnames = [room for room in client.rooms.keys() if not room[:5] == "outsi"]

    #Scattering Items:
    channelswithitems = scrambled(random.sample(listofroomnames, len(client.items)))

    for i in range(len(client.items)):
        item = client.items[i]
        Roomclass = client.rooms[channelswithitems[i]][0]
        await Roomclass.additem(item)

    #Fuel Barrels and Narrels:
    Fuelslist = scrambled(client.Fuelslist)
    fuelrooms = ["garage", "shed", "outside-shed", "outside-heli-upper", "outside-heli-bottom", "outside-dog-shed", "storage"]
    channelswithfuels = random.sample(fuelrooms, len(Fuelslist))
    for i in range(len(Fuelslist)):
       item = Fuelslist[i]
       Roomclass = client.rooms[channelswithfuels[i]][0]
       await Roomclass.additem(item)
    
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Items", value = "Items were scattered around the map!", inline = False))

    #Players :
    adminrole = discord.utils.get(ctx.guild.roles, name = ADMINROLENAME)
    Playerslist = scrambled([player for player in ctx.guild.members if (not adminrole in player.roles) and (not player.bot)])
    playersnamelist = [player.name for player in Playerslist]
    numberofplayers = len(playersnamelist)

    await setupembedmsg.edit(embed = setupembed.add_field(name = "Participating members : ", value = '\n'.join([f'{Player.mention} - {Player.name}' for Player in Playerslist]), inline = False))

    #All Character names
    Charactertypes = []
    for charname in DispatchedInfo["Characters"].keys():
        Characterclass = await Character.create(charname)
        Charactertypes.append(Characterclass)
        client.Characters[Characterclass.name] = Characterclass
    UsedCharacters = scrambled(random.sample(Charactertypes, numberofplayers))
    PlayerRoomnames = scrambled(random.sample(listofroomnames, numberofplayers))
    PlayerStartRooms = [client.rooms[roomname][0] for roomname in PlayerRoomnames]

    UsedPrivChannels = scrambled(await privChannels(ctx, numberofplayers))

    #Give players their private channel, starting room, characters and nicknames. Initializing Player classes and adding them to client.rooms
    for i in range(numberofplayers):
        membertype = Playerslist[i]
        Privatechanneltype = UsedPrivChannels[i]
        Roomtype = PlayerStartRooms[i]
        Charactertype = UsedCharacters[i]
        Playerclass = await Player.create(ctx, membertype, Privatechanneltype, Roomtype, Charactertype)
        client.Players[Playerclass.name] = Playerclass
        client.rooms[Playerclass.Room.name][1].append(Playerclass)
    
    #Giving Entity to a random player
    EntityPlayer = random.choice([Player for player, Player in client.Players.items()])
    EntityEmbed = discord.Embed(title = "The Entity", description = "\n".join(DispatchedInfo["Entity"]["Abilities"])).set_image(url = DispatchedInfo["Entity"]["image_url"])
    await EntityPlayer.giveEntity(EntityEmbed)

    playerinfoloaded = [(f"{Playertype.membertype.mention} - {playername} was placed in {Playertype.roomrole}. They're in the private channel {Playertype.playerchannel.mention} and were given the character {Playertype.Character.name}.") for playername, Playertype in client.Players.items()]
    await ctx.send("\n".join(playerinfoloaded))
    await ctx.send(f'{EntityPlayer.membertype.mention} - {EntityPlayer.name} ({EntityPlayer.nickname}) **is the Entity**.')
    
    #Send completion messages
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Placing players in ...", value = "... their private channel\n... their Starting room", inline = False))
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Giving players ...", value = "... their Characters' embeds\n... their nicknames",inline = False))
    await setupembedmsg.edit(embed = setupembed.add_field(name = "Setup Complete !", value = f"Ask players to change their profile pictures !\nSetup took {round(time.time() - starttime,1)}s.",inline = False))
    
    print("Setup complete.")
    return

@commands.has_role(ADMINROLENAME)
@client.command(name = "changechar")
async def _changechar(ctx, *args):
    charactername = ' '.join(args)
    character_type = client.Characters[charactername]
    player_type = await findplayer(ctx)
    
    await player_type.charembedmsg.delete()
    await player_type.addChar(character_type)
    await ctx.send(embed = character_type.embed.set_footer(text = "Please change your profile picture to the one shown above. Do .info for more information on your Character's abilities and general information about Dispatched."))
    return


@commands.has_role(ADMINROLENAME)
@client.command(name = "move", aliases = ["m", "moveto"])
async def _move(ctx, channelname):
    #abbreviations:
    abbreviationsdict = {
        "ds" : "dog-shed",
        "h" : "helicopter",
        "lh" : "lower-hallway",
        "ms" : "mini-storage",
        "rm" : "restroom",
        "st" : "storage",
        "sh" : "shed",
        "k" : "kitchen",
        "d" : "dorms",
        "l" : "lounge",
        "g" : "garage",
        "mh" : "middle-hallway",
        "uh" : "upper-hallway",
        "lab" : "laboratory",
        "ods" : "outside-dog-shed",
        "ohb" : "outside-heli-bottom",
        "ohu" : "outside-heli-upper",
        "os" : "outside-shed",
        "r" : "restroom",
        "ohr" : "outside-heli-bottom"
    }

    #allowedrooms:
    allowedrooms = allowedroomsdict()

    if channelname in abbreviationsdict.keys():
        channelname = abbreviationsdict[channelname]

    #find the player that is in this channel
    Playertype = await findplayer(ctx)

    if Player == None:
        msg = await ctx.send("No player has this channel as their private channel.")
        await msg.delete(delay = 3)
        await ctx.message.delete()
        return
    
    #Create string for channel options
    stringforchanneloptions = "The following rooms are available : "
    options = allowedrooms[Playertype.Room.name]
    numberofconnectedrooms = len(options)
    if numberofconnectedrooms == 1:
        channel = discord.utils.get(ctx.guild.text_channels, name = options[0])
        stringforchanneloptions = f"The following room is available : {channel.mention}."
    else:
        for i in range(numberofconnectedrooms):
            channel = discord.utils.get(ctx.guild.text_channels, name = options[i])
            if numberofconnectedrooms - 1 == i:
                stringforchanneloptions += f'and {channel.mention}.'
            else:
                #print(channel.name)
                stringforchanneloptions += f'{channel.mention}, '

    #Find the channel's Roomtype:
    try:
        Roomtype = client.rooms[channelname][0]
    except KeyError:
        msg = await ctx.send(f"This channelname isn't valid. Make sure to use uncapitalized words with hyphens in between.\n{stringforchanneloptions}")
        await msg.delete(delay = 5)
        await ctx.message.delete()
        return

    #check if the room the player is moving to is different from the one they currently are in
    if Playertype.Room == Roomtype:
        msg = await ctx.send(f"{Playertype.Character.name} is not even moving ! Pick a different channel than the one you're already in.\n{stringforchanneloptions}")
        await msg.delete(delay = 5)
        await ctx.message.delete()
        return
    
    #check if the room the player wants to move to is next to the one they currently are in
    if not Roomtype.name in allowedrooms[Playertype.Room.name]:
        msg = await ctx.send(f"This room is not connected to {Playertype.Room.roomrole}.\n{stringforchanneloptions}")
        await msg.delete(delay = 5)
        await ctx.message.delete()
        return
    
    #move the player if everything is in order
    client.rooms[Playertype.Room.name][1].remove(Playertype)
    await Playertype.Room.roomchat.send(f'*{Playertype.Character.name} leaves toward {Roomtype.roomrole.name}*')
    await Roomtype.roomchat.send(f'*{Playertype.Character.name} enters from {Playertype.Room.roomrole.name}*')
    await Playertype.moveroom(Roomtype)
    client.rooms[channelname][1].append(Playertype)
    await ctx.message.delete()
    await ctx.send(f"Player {Playertype.membertype.mention} - {Playertype.Character.name} was moved to {Roomtype.roomrole.name}")


@client.command(name = "info")
async def _info(ctx, *, infotype = None):
    DispatchedInfo = await openDispatchedInfojson()
    Playertype = client.Players[ctx.message.author.name]
    
    #if done in a room:
    if ctx.message.channel.name[:3] != "pla":
        await ctx.message.delete()
        await Playertype.playerchannel.send(f"{Playertype.membertype.mention} Don't send commands in the Rooms please.")
        return

    #Basic .info command
    if infotype == None:
        embed = discord.Embed(title = "Information")
        for key in DispatchedInfo["Information"].keys():
            if not( (key[-3:] == "map") or (key == "Dispatched_image") ):
                embed.add_field(name = key, value = f"Do .info {key} for information about {key}", inline = False)
            #embed.add_field(title = "Abilities", value = f'Do .info abilities for information about your Character\'s abilities.', inline = False)
            #same for items
        if Playertype.isEntity:
            embed.add_field(name = "Entity info", value = "Do .info Entity for more imformation about the Entity's abilities.", inline=False)

    #.info <word> for more specific information        
    elif infotype:
        if infotype in [key for key in DispatchedInfo["Information"].keys() if not ((key[-3:] == "map") or (key == "Dispatched_image") or key == "setting")]:
            embed = discord.Embed(title = infotype, description = DispatchedInfo["Information"][infotype])
        if infotype == "setting":
            embed = discord.Embed(title = infotype, description = DispatchedInfo["Information"][infotype]).set_image(url = "https://cdn.discordapp.com/attachments/746472259517939813/800676660310441984/the_thing_banner.jpg")
        elif infotype == "abilities":
            #add when DispatchedInfo.json is fixed (all abilities are there). Only show abilities of the player's character with Playertype.Character.name for the character's name
            embed = discord.Embed(title = "uhh this embed still needs to be created")
        elif infotype == "items":
            #add when DispatchedInfo.json is fixed (all items are there)
             embed = discord.Embed(title = "uhh this embed still needs to be created")
        elif infotype == "Entity" and Playertype.isEntity:
            Entitydict = DispatchedInfo["Entity"]
            embed = discord.Embed(title = infotype, description= Entitydict["Description"])
            for abilityname in DispatchedInfo["Entity"]["Abilities"]:
                embed.add_field(name = abilityname, value = DispatchedInfo["Abilities"][abilityname], inline = False)
        else:
            embed = discord.Embed(title = "This command does not exist. Try again.")
    else:
        embed = discord.Embed(title = "Invalid info type. Try again.")

    #send the embed
    await ctx.send(embed = embed)


@commands.has_role(ADMINROLENAME)
@client.command(name = "removeroles")
async def _removeroles(ctx, ADMINROLENAME = ADMINROLENAME, write_out = True):
    adminrole = discord.utils.get(ctx.guild.roles, name = ADMINROLENAME)
    [await member.edit(roles = []) for member in ctx.guild.members if (not adminrole in member.roles) and (not member.bot)]
    if write_out:
        await ctx.send("All members besides admins and bots had their roles removed.")


@commands.has_role(ADMINROLENAME)
@client.command(name = "ping")
async def _ping(ctx):
    start_time = time.time()
    message = await ctx.send(f'Testing Ping...')
    end_time = time.time()
    await message.edit(content = f"Pong! {round(client.latency * 1000)}ms\nAPI: {round((end_time - start_time) * 1000)}ms")


@commands.has_role(ADMINROLENAME)
@client.command(name = "clear")
async def _clear(ctx, amount = 2):
    await ctx.channel.purge(limit = amount + 1)
    message = await ctx.send(f'{amount} messages successfully purged.')
    await(message.delete(delay=3))


"""

FUNCTIONS

"""

"""
ASYNC FUNCTIONS
"""

async def findplayer(ctx):
    try:
        for key, value in client.Players.items():
            if value.playerchannel.name == ctx.message.channel.name:
                return value
    except:
        return None


async def chnick(ctx, member: discord.Member, nick):
    try:
        await member.edit(nick=nick)
    except discord.errors.Forbidden:
        await ctx.send(f'Failed to change {member.mention}\'s nickname to {nick}.')


async def delall(ctx):
    roomslist = []
    private_rooms_list = []
    start = time.time()
    roomcategories = ["Outside", "Facility"]
    playerchancategories = ["Players 1", "Players 2", "Dead Players"]
    
    for category in ctx.message.guild.categories:
        if category.name in roomcategories:
            for channel in category.text_channels:
                if channel.name[0] == "_":
                    room = await replacechan(ctx, latestroomchannel)
                    roomitems = await replacechan(ctx, channel)

                    for role in ctx.guild.roles:
                        if strip(role.name) == latestroomchannel.name:
                            roomrole = role

                    roomclass = await Room.create(room, roomitems, roomrole)
                    roomslist.append(roomclass)
                else:
                    latestroomchannel = channel
        if "Players 1" == category.name:
            Players1 = category
        elif "Players 2" == category.name:
            Players2 = category
        elif "Dead Players" == category.name:
            DeadPlayers = category
            break
        
    playerchannels = []
    channelnames = ["player-1", "player-2", "player-3", "player-4", 
    "player-5", "player-6","player-7","player-8","player-9"]
    channellistwithprivatechannels = [channel for channel in Players1.text_channels if channel.name in channelnames and not len(await channel.history().flatten()) == 0] \
        + [channel for channel in Players2.text_channels if channel.name in channelnames and not len(await channel.history().flatten()) == 0] \
            + [channel for channel in DeadPlayers.text_channels if channel.name in channelnames and not len(await channel.history().flatten()) == 0]
    
    for channelname in channelnames[:len(channellistwithprivatechannels)][::-1]:
        for private_channel in channellistwithprivatechannels:
            if private_channel.name == channelname:
                new_private_channel = await private_channel.clone()
                await private_channel.delete()
                await new_private_channel.move(category = Players1, beginning = True)
    private_rooms_list += [channel for channel in Players1.text_channels]

    timespent = time.time() - start
    return roomslist, private_rooms_list, timespent


async def replacechan(ctx, channel):
    newchannel = await channel.clone()
    await channel.delete()
    return newchannel

"""
MAYBE USELESSLY ASYNC?
"""

async def findrole(ctx, channel):
    for role in ctx.guild.roles:
        if strip(role.name) == channel.name:
            return role

async def findchannel(ctx, itemschannel):
    listoftextchannels = ctx.guild.text_channels
    for i in range(len(listoftextchannels)):
        if listoftextchannels[i] == itemschannel:
            return listoftextchannels[i - 1]

async def privChannels(ctx, numberofplayers):
    Playercategories = ["Players 1", "Players 2"]
    Privchannels = []
    for category in ctx.guild.categories:
        if category.name == "Players 1":
        #if category.name in Playercategories:
            if category.channels != None:
                for i in range(numberofplayers):
                    Privchannels.append(category.channels[i])
    return Privchannels


async def openDispatchedInfojson():
    with open('DispatchedInfo.json', "r") as f:
        DispatchedInfo = json.load(f)
    return DispatchedInfo


"""
NORMAL FUNCTIONS
"""

def strip(string):
    string = string.lower()
    resultlst = list(string)
    for i in range(len(resultlst)):
        if resultlst[i] == " ":
            resultlst[i] = "-"
    result = "".join(resultlst)
    return result


def scrambled(orig):
    dest = orig[:]
    random.shuffle(dest)
    return dest


def allowedroomsdict():
    Rooms = {
        "shed" : ["outside-shed"],
        "outside-shed" : ["shed", "garage", "outside-heli-upper"],
        "outside-heli-upper" : ["helicopter", "outside-shed", "dorms"],
        "helicopter" : ["outside-heli-upper", "outside-heli-bottom"],
        "outside-heli-bottom" : ["helicopter", "outside-dog-shed"],
        "dorms" : ["outside-heli-upper", "restroom", "middle-hallway"],
        "restroom" : ["dorms"],
        "garage" : ["outside-shed", "upper-hallway"],
        "upper-hallway" : ["garage", "middle-hallway", "lounge", "laboratory"],
        "middle-hallway" : ["mini-storage", "dorms", "upper-hallway", "lounge"],
        "mini-storage" : ["middle-hallway"],
        "lounge" : ["middle-hallway", "upper-hallway", "lower-hallway", "kitchen"],
        "lower-hallway" : ["lounge", "storage", "outside-dog-shed"],
        "outside-dog-shed" : ["outside-heli-bottom", "dog-shed", "lower-hallway"],
        "storage" : ["lower-hallway"],
        "kitchen" : ["lounge"],
        "laboratory" : ["upper-hallway"],
        "dog-shed" : ["outside-dog-shed"]
    }
    return Rooms

#enter the token for the client here
client.run("token")