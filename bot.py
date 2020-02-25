import discord
import os
import json
import discord
from discord.ext import commands, tasks
from itertools import cycle

import bs4 as bs
import urllib.request


def update_soup_cache():
    status_page_url = 'https://status.mixer.com/'
    sauce = urllib.request.urlopen(status_page_url).read()
    soup = bs.BeautifulSoup(sauce, 'lxml')
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/status_cache.html", "w", encoding='utf-8') as cache:
        cache.write(str(soup))
    print('Cache saved')

def get_soup_from_cache():
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/status_cache.html", "r", encoding='utf-8') as cache:
        soup = bs.BeautifulSoup(cache, 'lxml')
    return(soup)


def get_status(soup):
    status = soup.find('span', class_='status')
    status = status.text.strip()
    return(status)

def get_status_bool(soup):
    status = soup.find('span', class_='status').text.strip()
    if 'All Systems Operational' in status:
        status_bool = True
    else:
        status_bool = False
    return(status_bool)

def get_detailed_status(soup):
    status_detailed  = {}
    statuses = soup.find_all('div', class_='component-inner-container')

    for item in statuses:
        name = item.find('span', class_='name').text.strip()
        status = item.find('span', class_='component-status').text.strip()
        status_detailed.update({name : status})
    return(status_detailed)

def get_last_incident(soup):
    #Coming soon
    return('Coming soon...')

#Startup
with open(f'{os.path.dirname(os.path.realpath(__file__))}/settings.json') as f:
    settings = json.load(f)    
TOKEN = settings["TOKEN"]
mode = settings["mode"]
prefix = settings["prefix"]
default_game = settings["default_game"]
client = commands.Bot(command_prefix = prefix)


#Startup
@client.event
async def on_ready():
    print(f'{client.user.name} online!')
    save_cache.start()
    update_bot_status.start()


#Tasks
@tasks.loop(minutes=10)
async def save_cache():
    print('Updating local cache')
    update_soup_cache()

@tasks.loop(minutes=10)
async def update_bot_status():
    status_bool = get_status_bool(get_soup_from_cache())
    status = get_status(get_soup_from_cache())
    if status_bool == True:
        print('Everything is fine')
        await client.change_presence(status=discord.Status.online, activity=discord.Game(status))
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/img/green.jpg', 'rb') as img:
            await client.user.edit(avatar=img.read())
    else:
        print('Something is on fire')
        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(status))
        with open(f'{os.path.dirname(os.path.realpath(__file__))}/img/yellow.jpg', 'rb') as img:
            await client.user.edit(avatar=img.read())


#Root Commands
@client.command()
async def status(ctx):
    status = get_status(get_soup_from_cache())
    await ctx.send(status)
    

#Cog managment
@client.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded {extension} extension.')

@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension='null'):
    if extension == 'null':
        await ctx.send(f'No extension name specified.')
    else:
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloaded {extension} extension.')

@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension='null'):
    if extension == 'null':
        await ctx.send(f'No extension name specified.')
    else:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reloaded {extension} extension.')

@client.command(hidden=True)
@commands.is_owner()
async def listcogs(ctx):
    cogs = []
    for filename in os.listdir(f'{os.path.dirname(os.path.realpath(__file__))}/cogs'):
        if filename.endswith('.py') and filename == 'functions.py':
            cogs.append(f'{filename[:-3]}')
    await ctx.send(f'Found these cogs:\n{cogs}')

for filename in os.listdir(f'{os.path.dirname(os.path.realpath(__file__))}/cogs'):
    if filename.endswith('.py') and filename != 'functions.py':
        client.load_extension(f'cogs.{filename[:-3]}')


#Run
client.run(TOKEN)