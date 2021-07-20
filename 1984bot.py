import discord
import numpy as np
import pandas as pd
import os
import sys
from dotenv import load_dotenv
from discord.ext import commands
import random
from discord.ext.commands import has_permissions, MissingPermissions
from discord.utils import get
import re
import math

intents = discord.Intents.default()
intents.members = True

load_dotenv()
token = os.getenv('discordToken')

bot = commands.Bot(command_prefix = ['1984bot, ', '$', '\`'], intents = intents)

rulesFilePath = 'rules.csv'
blacklistFilePath = 'blacklist.csv'
violationsFilePath = 'violations.csv'

if os.path.exists(rulesFilePath) == True:
    rulesDF = pd.read_csv(rulesFilePath, sep = ';')
    rulesDF.set_index('index', inplace = True)
else:
    rulesDF = pd.DataFrame(index = range(2), columns = ['ID', '1'])
if os.path.exists(blacklistFilePath) == True:
    blacklistDF = pd.read_csv(blacklistFilePath, sep = ';')
    blacklistDF.set_index('index', inplace = True)
else:
    blacklistDF = pd.DataFrame(index = range(3), columns = ['ID', 'test'])
if os.path.exists(violationsFilePath):
    violationDF = pd.read_csv(violationsFilePath)
else:
    violationDF = pd.DataFrame(index = range(3), columns = ('Violation', 'Priority', 'Pattern'))

newMemberKeys = {}
blacklistSuggestions = []

@bot.event
async def on_ready():
    print('ONLINE')
    global ctds, nick, welcomeChannel, logChannel, shoelaceChannel, memberRole, ignoredChannelsID, noUptumblrID, ignoredChannels, noUptumblr
    ctds = bot.get_guild(808811670327263312)
    nick = os.path.splitext(sys.argv[0])[0]
    
    welcomeChannel = ctds.system_channel
    if welcomeChannel is None: welcomeChannel = bot.get_channel("welcome-channel")
    logChannel = bot.get_channel(829010774231744513)
    shoelaceChannel = bot.get_channel(843198731565662250)
    memberRole = ctds.get_role(835601075541245952)
    ignoredChannels = [808824429824049173, 851848452022992936, 851191799464984646, 856916672941916210, 822836922036387880, 854814653880598528]
    noUptumblr = [813499480518426624, 809854730632691712, 854814653880598528]
    print('VARS DECLARED')


'''
DISCORD BOT
- Word Highlight (Maybe find some way to fit into other blacklist too)
- Cone/Kick/Ban message
- Reaction Roles / Role Commands
- Add/Remove blacklist
- Join/Leave message
'''

'''
Blacklist structure
    Message containing blacklist
    File containing blacklist and keywords [class, topic, 'clarification', [keywords]]
        on initialization, all keywords added to a list
    Add command: classification, topic, clarification, keywords
    remove command: class and index/topic
    Edit command: class, topic, revision field 1, etc
        Revision field can be skipped with ^ character
    View command: class, topic; returns keywords
'''

def blEmbedUpdate():
    phobiaEmbed = discord.Embed(title = 'Phobias', color = discord.Color.dark_theme())
    atEmbed = discord.Embed(title = 'Avoided Topics', color = discord.Color.dark_theme())
    triggerEmbed = discord.Embed(title = 'Triggers', color = discord.Color.dark_theme())
    for column in sorted(blacklistDF.columns[1:]):
        if blacklistDF.at[1, column] == '0':
            triggerEmbed.add_field(name = str(column), value = str(blacklistDF.at[0, column]), inline = False)
        elif blacklistDF.at[1, column] == '1':
            phobiaEmbed.add_field(name = str(column), value = str(blacklistDF.at[0, column]), inline = False)
        elif blacklistDF.at[1, column] == '2':
            atEmbed.add_field(name = str(column), value = str(blacklistDF.at[0, column]), inline = False)
        else:
            print('FUCKED IT UP')
    return triggerEmbed, phobiaEmbed, atEmbed

async def blUpdate(triggerEmbed, phobiaEmbed, atEmbed):
    blChannel = bot.get_channel(int(blacklistDF.columns[0]))
    triggerMsg = await blChannel.fetch_message(id = blacklistDF.at[0, blacklistDF.columns[0]])
    phobiaMsg = await blChannel.fetch_message(id = blacklistDF.at[1, blacklistDF.columns[0]])
    atMsg = await blChannel.fetch_message(id = blacklistDF.at[2, blacklistDF.columns[0]])
    await triggerMsg.edit(embed = triggerEmbed)
    await phobiaMsg.edit(embed = phobiaEmbed)
    await atMsg.edit(embed = atEmbed)
    blacklistDF.to_csv(blacklistFilePath, sep = ';')

triggerEmbed, phobiaEmbed, atEmbed = blEmbedUpdate()
print('BLACKLIST GENERATED')

@bot.command(name = 'secure', aliases = ['blCreate', 'bC', 'blacklist', 'blacklistCreate'], help = 'ENSURE SAFETY OF ENVIRONMENT')
@has_permissions(kick_members = True)
async def blacklistCreator(ctx):
    #print('COMMAND RECEIVED')
    triggerEmbed, phobiaEmbed, atEmbed = blEmbedUpdate()
    triggerMsg = await ctx.send(embed = triggerEmbed)
    phobiaMsg = await ctx.send(embed = phobiaEmbed)
    atMsg = await ctx.send(embed = atEmbed)
    originalID = blacklistDF.columns[0]
    blacklistDF.rename(columns = {originalID: 'ID'}, inplace = True)
    blacklistDF.at[0, 'ID'] = triggerMsg.id
    blacklistDF.at[1, 'ID'] = phobiaMsg.id
    blacklistDF.at[2, 'ID'] = atMsg.id
    blacklistDF.rename(columns = {'ID': str(ctx.channel.id)}, inplace = True)
    blacklistDF.index.name = 'index'

@bot.command(name = 'aggregate:', aliases = ['addBL', 'aB', 'addBlacklist'], help = 'ADD SAFETY PARAMETERS')
@has_permissions(kick_members = True)
async def newBL(ctx, subject, descrip, field, *keywords):
    if field.lower() == 'trigger':
        field = '0'
    elif field.lower() == 'phobia':
        field = '1'
    elif field.lower() == 'avoided':
        field = '2'
    else:
        raise
    blacklistDF.at[0, subject] = descrip
    blacklistDF.at[1, subject] = field
    for keyword in keywords:
        blacklistKeywords.append(keyword)
    sep = ' '
    keywordJoined = sep.join(keywords)
    blacklistDF.at[2, subject] = keywordJoined
    triggerEmbed, phobiaEmbed, atEmbed = blEmbedUpdate()
    await blUpdate(triggerEmbed, phobiaEmbed, atEmbed)

@bot.command(name = 'diverge:', aliases = ['removeBL', 'rB', 'removeBlacklist', 'delBlacklist', 'deleteBlacklist'], help = 'REMOVE RESTRICTION')
@has_permissions(kick_members = True)
async def subtractBL(ctx, index):
    keywordJoined = blacklistDF.at[2, index]
    if isinstance(keywordJoined, str) == True:
        keywords = keywordJoined.split(' ')
        for keyword in keywords:
            if keyword in blacklistKeywords:
                blacklistKeywords.remove(keyword)
    blacklistDF.pop(index)
    triggerEmbed, phobiaEmbed, atEmbed = blEmbedUpdate()
    await blUpdate(triggerEmbed, phobiaEmbed, atEmbed)

@bot.command(name = 'suggest', aliases = ['blS', 'blSuggest', 'blacklistSuggestion'], help = 'COMMUNITY SOURCING')
async def suggestBL(ctx, field, subject, *descrips):
    if field.lower() != 'avoided':
        if field.lower() != 'phobia':
            if field.lower() != 'trigger':
                await ctx.send('Incorrect field type. Reformat.')
                return
    
    blSuggestEmbed = discord.Embed(title = 'New ' + field, color = discord.Color.dark_theme()) 
    sep = ' '
    blSuggestEmbed.add_field(name = subject, value = sep.join(descrips), inline = False)
    blSuggestEmbed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
    message = await logChannel.send(embed = blSuggestEmbed)
    await message.edit(content = str(message.id), embed = blSuggestEmbed)
    blacklistSuggestions.append([message.id, subject, sep.join(descrips), field])

@bot.command(name = 'accept', aliases = ['blAcc', 'blAccept', 'blacklistAccept'], help = 'VALIDATION AND APPROVAL')
@has_permissions(kick_members = True)
async def acceptBL(ctx, ID, *keywords):
    for ticket in blacklistSuggestions:
        if ticket[0] == int(ID):
            await newBL(ctx, ticket[1], ticket[2], ticket[3], *keywords)
            blacklistSuggestions.remove(ticket)
            
'''
Rules structure
    Message containing rules
    Add command: 'rule'(, reindex number)
    Remove command: index
    Edit command: index, 'rule'
'''

def rulesEmbedUpdate():
    rulesEmbed = discord.Embed(title = 'Rules List', color = discord.Color.dark_theme())
    for column in sorted(rulesDF.columns[1:], key = int):
        rulesEmbed.add_field(name = str(column) + '. ' + str(rulesDF.at[0, column]), value = str(rulesDF.at[1, column]), inline = False)
    return rulesEmbed

async def rulesUpdate(rulesEmbed):
    rulesChannel = bot.get_channel(rulesDF.at[0, 'ID'])
    rulesMsg = await rulesChannel.fetch_message(id = rulesDF.at[1, 'ID'])
    await rulesMsg.edit(embed = rulesEmbed)
    rulesDF.to_csv(rulesFilePath, sep = ';')

rulesEmbed = rulesEmbedUpdate()
print('RULES GENERATED')

@bot.command(name = 'administrate', aliases = ['rulesCreate', 'rC', 'rules'], help = 'ESTABLISH LAW AND ORDER')
@has_permissions(kick_members = True)
async def rulesCreator(ctx):
    #print('COMMAND RECEIVED')
    rulesEmbed = rulesEmbedUpdate()
    rulesMsg = await ctx.send(embed = rulesEmbed)
    rulesDF.at[1, 'ID'] = rulesMsg.id
    rulesDF.at[0, 'ID'] = ctx.channel.id
    rulesDF.index.name = 'index'

@bot.command(name = 'directive:', aliases = ['addRule', 'aR'], help = 'EXPAND LEGISLATURE')
@has_permissions(kick_members = True)
async def newRule(ctx, mainRule, descrip, index = None):
    if index == None:
        index = len(rulesDF.columns)
    else:
        index = int(index)
        for column in reversed(sorted(rulesDF.columns[1:], key = int)[index-1:]):
            rulesDF.rename(columns = {column: str(int(column)+1)}, inplace = True)
    rulesDF.at[0, str(index)] = mainRule
    rulesDF.at[1, str(index)] = descrip
    rulesEmbed = rulesEmbedUpdate()
    await rulesUpdate(rulesEmbed)

@bot.command(name = 'removal:', aliases = ['removeRule', 'rR', 'delRule', 'deleteRule', 'subtractRule'], help = 'STREAMLINE LEGISLATURE')
@has_permissions(kick_members = True)
async def subtractRule(ctx, index):
    rulesDF.pop(index)
    for column in sorted(rulesDF.columns[1:], key = int)[int(index)-1:]:
        rulesDF.rename(columns = {column: str(int(column)-1)}, inplace = True)
    rulesEmbed = rulesEmbedUpdate()
    await rulesUpdate(rulesEmbed)
    

'''
Word Highlight
    for keyword in blacklist:
        if msgcontent.contains(keyword):
            violationList.append(keyword)
    send message in mod channel "message (copy) violates these keywords: [violationList]"
'''

async def indoctrination(message):
    if not message.channel == shoelaceChannel: return
    for user, code in newMemberKeys.items():
        if message.author.id == user and message.content == str(code):
            await message.author.add_roles(memberRole)
            welcomeEmbed = discord.Embed(title = 'New member', url = message.jump_url, description = f'Welcome to the server, {message.author.mention}!', color = discord.Color.dark_gold())
            welcomeEmbed.set_author(name = message.author.name, icon_url = message.author.avatar_url)
            await shoelaceChannel.send(embed = welcomeEmbed)
            newMemberKeys.pop(user)
            break

async def randUptumblr(message):
    if message.channel.id in noUptumblr: return
    if random.random() < 0.0001:
        await message.add_reaction("<:uptumblr:810019271215677441>")

async def beppening(message):
    content = parseContent(message)
    if 'bep' in content: await message.add_reaction(bot.get_emoji(824743021434241054))

def parseContent(message):
    string = message.content.lower()
    # All below replaces characters in a string (common substitutions) to prevent people from escaping the blacklist
    replaceDict = {
        '[\u200B-\u200F\u2028-\u2029\uFEFF]': '', # Zero-width characters
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        'ñ': 'n',
        '7': 't',
        '0': 'o',
        '8': 'b',
        '&': 'and',
        'wanna': 'want to',
        r'\bur': 'your',
        '\U0001F447': 'your',
        '-': ' ',
        '–': ' ',
        '—': ' ',
        '_': ' ',
        '\U0001f170': 'a',
        '\U0001f171': 'b',
        '\U0001f17e': 'o',
        '\U0001f1e6': 'a',
        '\U0001f1e7': 'b',
        '\U0001f1e8': 'c',
        '\U0001f1e9': 'd',
        '\U0001f1ea': 'e',
        '\U0001f1eb': 'f',
        '\U0001f1ec': 'g',
        '\U0001f1ed': 'h',
        '\U0001f1ee': 'i',
        '\U0001f1ef': 'j',
        '\U0001f1f0': 'k',
        '\U0001f1f1': 'l',
        '\U0001f1f2': 'm',
        '\U0001f1f3': 'n',
        '\U0001f1f4': 'o',
        '\U0001f1f5': 'p',
        '\U0001f1f6': 'q',
        '\U0001f1f7': 'r',
        '\U0001f1f8': 's',
        '\U0001f1f9': 't',
        '\U0001f1fa': 'u',
        '\U0001f1fb': 'v',
        '\U0001f1fc': 'w',
        '\U0001f1fd': 'x',
        '\U0001f1fe': 'y',
        '\U0001f1ff': 'z',
        '\u262a': 'c',
        '\u2653': 'h',
        '\u2139': 'i',
        '\u264d': 'm',
        '\u264f': 'm',
        '\u2651': 'n',
        '\u2b55': 'o',
        '\U0001f17f': 'p',
        '\u271d': 't',
        '\u2626': 't',
        '\u26ce': 'u',
        '\u2648': 'v',
        ' ': ' ',
        ' ': ' ',
        r'\n': ' ',
        '[^\x20-\x7F]': '',
        r'(https?)(:\/\/.*?\/)': '\\1\u200B\\2'
    }

    for replaceFrom, replaceTo in replaceDict.items():
        string = re.sub(replaceFrom, replaceTo, string)
    return string

async def logViolation(message, fromEvent = 'sent'):
    if message.channel.id in ignoredChannels: return
    channel = logChannel
    content = parseContent(message)
    
    violationList = []
    containedWords = set()
    
    for word, pattern in zip(violationDF.iloc[:, 0], violationDF.iloc[:, 2]):
        found = re.findall(pattern, content)
        if found:
            containedWords.update(found)
            violationList.append(word)
    if len(violationList) == 0: return
    
    ping = ' ' # decide priority here
    
    # This is where the double loops will be going
    # Double loops are replacing the following bit
    content = content[:256] if len(content) <= 256 else f'{content[:128]}...\n[See more ...]({message.jump_url})'
    for word in containedWords:
        content = re.sub(word, f'[**{word}**]({message.jump_url})', content)
    
    alert = f'{message.author.name} {fromEvent} [a message]({message.jump_url}) containing: ' + ', '.join(set(containedWords))
    
    embed = discord.Embed(title = 'Violation: ' + ', '.join(violationList), description = content, color = discord.Color.dark_gold())
    embed.set_author(name = message.author.name, icon_url = message.author.avatar_url)
    embed.add_field(name = '\u200b', value = alert, inline = True)
    
    if len(message.attachments) == 0:
        attachments = None
        attachmentLinks = [' ']
    elif len(message.attachments) == 1 and message.attachments[0].size < 8388608:
        attachments = await message.attachments[0].to_file()
        attachmentLinks = [' ']
    else:
        attachments = None
        attachmentLinks = [file.url for file in message.attachments]
    
    await channel.send(content = ping + '\n'.join(attachmentLinks), file = attachments, embed = embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user or message.author.bot:
        return
    await indoctrination(message)
    await randUptumblr(message)
    await beppening(message)
    await logViolation(message)

@bot.event
async def on_raw_message_edit(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(id = payload.message_id)
    if message.author == bot.user or message.author.bot:
        return
    await beppening(message)
    await logViolation(message)
    
'''
Cone/Ice
    log cone/ice update
    if being added, send message in mod channel "hey! user just got coned/iced! length and reason?"
    upon reply, post reason and punishment in #rulebreaker-central
    set timer for length, automatically remove cone/ice at end
        length can be omitted with ^ character
'''

'''
Kick/ban
    log kick/ban
    send mod channel msg "hey! user got kicked/banned! reason?"
    dm user with reason
'''

'''
Join/Leave
    on join, dm members a copy of the rules
        add string "Randomly placed string to thwart bots! paste this into #shoelace to join" in certain spots randomly
    append user and random string added to list
    a msg from user containing string gives member role and removes them from list
    purge list every 24 hours
    on leave, immortalize their shame.
'''

@bot.event
async def on_member_join(member):
    rulesEmbed = discord.Embed(title = 'Rules List', url = 'https://docs.google.com/document/d/1vqxfYxO2mtPh0O7rrgOTUx0UtW3a6vDyXjYclI2n5X8/edit?usp=sharing', color = discord.Color.dark_theme())
    columns = sorted(rulesDF.columns[1:], key = int)
    rand_index = random.randint(0, len(columns)-1)
    randKey = random.randint(1000000, 9999999)
    for index in range(len(columns)):
        if rand_index == index:
            if str(rulesDF.at[1, columns[index]]) == '-----':
                rulesEmbed.add_field(name = f'{str(columns[index])}. {str(rulesDF.at[0, columns[index]])}', value = f'To access the server, paste {str(randKey)}', inline = False)
            else:
                rulesEmbed.add_field(name = f'{str(columns[index])}. {str(rulesDF.at[0, columns[index]])}', value = f'{str(rulesDF.at[1, columns[index]])} To access the server, paste {str(randKey)}', inline = False)
        else:
            rulesEmbed.add_field(name = str(columns[index]) + '. ' + str(rulesDF.at[0, columns[index]]), value = str(rulesDF.at[1, columns[index]]), inline = False)
    newMemberKeys[member.id] = randKey
    try: await member.send(f"Welcome to the Curated Tumblr Discord Server! To ensure you're not a bot, please read over the rules and paste the 7 digit key hidden in the rules into {shoelaceChannel.mention}. Upon doing so, you'll be able to access the rest of the server. Thanks, and have fun!", embed = rulesEmbed)     
    except:
        embed = discord.Embed(title = 'Oops!', description = "Looks like you don't have DMs enabled. Please enable them temporarily and rejoin the server.", color = discord.Color.dark_theme())
        embed.set_author(name = member.name, icon_url = member.avatar_url)
        await shoelaceChannel.send(content = member.mention,embed = embed)

@bot.command(name = 'resend', aliases = ['rS', 'resendWelcome'], help = 'REPEAT DECONTAMINATION PROCEDURES')
async def resend(ctx, member: discord.Member = None):
    if member == None:
        member = ctx.author
    await on_member_join(member)

@bot.command(name = 'activeKeys', aliases = ['viewActiveNewMemberKeys', 'aK', 'viewKeys'] , help = 'DISPLAY NEW MATERIAL')
@has_permissions(kick_members = True)
async def viewKeys(ctx):
    keyEmbed = discord.Embed(title = 'Active New Member Keys:', description = ' ' if len(newMemberKeys) else 'None', color = discord.Color.greyple())
    for userID, code in newMemberKeys.items():
        keyEmbed.add_field(name = bot.get_user(int(userID)).name, value = int(code), inline = False)
    await ctx.send(embed = keyEmbed)

@bot.event
async def on_member_remove(member):
    leaveEmbed = discord.Embed(title = 'Goodbye!', description = f'{member.mention} has left us <:whyy:812845017412272128>', color = discord.Color.greyple())
    leaveEmbed.set_author(name = member.name, icon_url = member.avatar_url)
    await welcomeChannel.send(embed = leaveEmbed)

'''
Reaction Roles
lol no idea how this works
'''

@bot.event
async def on_member_update(before, member):
    if member == bot.user:
        if member.guild.me.nick != nick:
            await member.guild.me.edit(nick = nick)

@bot.command(name = 'nick', aliases = ['nickname', 'nN', 'changenick', 'chnick'], help = 'REINDEX SUBJECT')
async def chnick(ctx, member: discord.Member = bot.user, *nickname):
    global nick
    newNick = ' '.join(nickname)
    if member == bot.user: nick = newNick
    await member.edit(nick = newNick)

@bot.command(name = 'ping', help = 'MONITOR CONNECTION')
async def ping(ctx):
    await ctx.send(f'Ping is {str(np.round(1000*bot.latency, 2))} ms')

@bot.command(name = 'reload', aliases = ['f5', 'refresh'], help = 'RELOAD')
async def reload(ctx):
    print('\nRELOADING ..........................\n')
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

@bot.command(name = 'disconnect', aliases = ['dc', 'logoff'], help = 'DEACTIVATE')
@has_permissions(kick_members = True)
async def disconnect(ctx):
    rulesDF.to_csv(rulesFilePath, sep = ';')
    blacklistDF.to_csv(blacklistFilePath, sep = ';')
    await bot.close()

bot.run(token)
