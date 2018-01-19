#!/usr/bin/env python3

import discord

import requests
import time
import datetime
import re

import threading

path = '/home/johnathans96/jimmybot/'

class Stream:
    def __init__(self, display_name, status, url):
        self.display_name = display_name
        self.status = status
        self.url = url
        self.time_fetched = time.time()
        self.ctime_fetched = time.ctime()

    def __str__(self):
        return "NOW LIVE : " + self.url + " | " + self.status

    def __eq__(self, other):
        return self.display_name == other.display_name

class Twitcher:
    def __init__(self):
        self.whitelist = [line.rstrip('\n').lower() for line in open(path + 'twitcher/whitelist.txt')]
        self.blacklist = [line.rstrip('\n').lower() for line in open(path + 'twitcher/blacklist.txt')]
        self.keywords = [line.rstrip('\n').lower() for line in open(path + 'twitcher/keywords.txt')]
        self.skipwords = [line.rstrip('\n').lower() for line in open(path + 'twitcher/skipwords.txt')]
        self.live = []
        self.cooldown = 60 * 10   # seconds

    def fetch_livestreams(self):
        ret = []
        streams = []

        self.log("Fetching streamlist")
        r = requests.get("https://api.twitch.tv/kraken/streams?game=Super%20Mario%2064")
        if not r:
            self.log("Failed to fetch streamlist")
            return None
        if 'streams' not in r.json():
            self.log("Streams not in r.json()")
            return None
        for stream in r.json()['streams']:
            display_name = stream['channel']['display_name'].lower()
            status = stream['channel']['status']
            url = '<' + stream['channel']['url'] + '>'

            if display_name in self.blacklist:
                continue
            if display_name not in self.whitelist:
                has_keyword = False
                for word in status.split():
                    if word.lower() in self.skipwords:
                        has_keyword = False     # checking for skipwords before keywords, uses var has_keyword if does
                        break
                    if word.lower() in self.keywords:
                        has_keyword = True      # no break because want to still check for skipwords 
                if has_keyword == False:
                    continue

            # puts links in code tags, removes discord links, and removes @ before a word
            for link in re.findall(r'(https?://[^\s]+)', status.lower()):
                status = status.replace(link, ''' + link + ''')

            for part in status.split():
                if 'discord.gg' in part:
                    status = status.replace(part, '<discord link>')

            for part in status.split():
                if part[0] == '@':
                    status = status.replace(part, part[1:])
                
            temp = Stream(display_name, status, url)
            if temp not in self.live:
                self.live.append(temp)
                ret.append(temp)
            streams.append(temp)

        for stream in list(self.live):
            if stream not in streams:
                if int(time.time()) > int(stream.time_fetched) + self.cooldown:
                    self.live.remove(stream)
                    self.log('Removing {} from live. (time fetched: {})'.format(stream.display_name, str(stream.ctime_fetched)))

        if not ret:
            return None
        return "\n".join(map(str, ret))

    def add_whitelist(self, user):
        user = user.lower()
        if user in self.whitelist:
            return None
        self.whitelist.append(user)
        with open(path + 'twitcher/whitelist.txt', 'a') as file:
            file.write(user + '\n')
        return user + ' added to whitelist.'

    def remove_whitelist(self, user):
        user = user.lower()
        self.whitelist.remove(user)
        with open(path + 'twitcher/whitelist.txt', 'w') as file:
            for u in self.whitelist:
                file.write(u + '\n')
        return user + ' removed from whitelist.'

    def add_blacklist(self, user):
        user = user.lower()
        if user in self.blacklist:
            return None
        self.blacklist.append(user)
        with open(path + 'twitcher/blacklist.txt', 'a') as file:
            file.write(user + '\n')
        return user + ' added to blacklist.'

    def remove_blacklist(self, user):
        user = user.lower()
        self.blacklist.remove(user)
        with open(path + 'twitcher/blacklist.txt', 'w') as file:
            for u in self.blacklist:
                file.write(u + '\n')
        return user + ' removed from blacklist'

    def add_keyword(self, word):
        word = word.lower()
        if word in self.keywords:
            return None
        self.keywords.append(word)
        with open(path + 'twitcher/keywords.txt', 'a') as file:
            file.write(word + '\n')
        return word + ' added as keyword.'

    def remove_keyword(self, word):
        word = word.lower()
        self.keywords.remove(word)
        with open(path + 'twitcher/keywords.txt', 'w') as file:
            for keyword in self.keywords:
                file.write(keyword + '\n')
        return word + ' no longer a keyword.'

    def add_skipword(self, word):
        word = word.lower()
        if word in self.skipwords:
            return None
        self.skipwords.append(word)
        with open(path + 'twitcher/skipwords.txt', 'a') as file:
            file.write(word + '\n')
        return word + ' added as skipword.'

    def remove_skipword(self, word):
        word = word.lower()
        self.skipwords.remove(word)
        with open(path + 'twitcher/skipwords.txt', 'w') as file:
            for skipword in self.skipwords:
                file.write(skipword + '\n')
        return word + ' no longer a skipword.'

    def get_whitelist_as_string(self):
        return 'whitelist: ' + ', '.join(self.whitelist)

    def get_blacklist_as_string(self):
        return 'blacklist: ' + ', '.join(self.blacklist)

    def get_keywords_as_string(self):
        return 'keywords: ' + ', '.join(self.keywords)

    def get_skipwords_as_string(self):
        return 'skipwords: ' + ', '.join(self.skipwords)

    def get_live_as_string(self):
        names = []
        for stream in self.live:
            names.append(stream.display_name)
        return 'live: ' + ', '.join(names)

    def log(self, s):
        s = time.ctime() + ":  " + s
        with open(path + 'logs/log_' + str(datetime.datetime.now().strftime("%Y_%m_%d")) + '.txt', 'a') as file:
            file.write(s + '\n')
        print(s)

def discord_bot():
    t = Twitcher()

    with open(path + 'user/info.txt') as file:
        email = file.readline().strip('\n')
        password = file.readline().strip('\n')

    client = discord.Client()
    client.login(email, password)

    mods = [line.rstrip('\n').lower() for line in open(path + 'bot/mods.txt')]
    channels = [line.rstrip('\n').lower() for line in open(path + 'bot/channels.txt')]

    def get_mods_as_string():
        return 'mods: ' + ', '.join(mods)

    def get_channels_as_string():
        return 'channels: ' + ', '.join(channels)

    def add_mod(user):
        user = user.lower()
        if user in mods:
            return None
        mods.append(user)
        with open(path + 'bot/mods.txt', 'a') as file:
            file.write(user + '\n')
        return user + ' added as mod.'

    def remove_mod(user):
        user = user.lower()
        mods.remove(user)
        with open(path + 'bot/mods.txt', 'w') as file:
            for mod in mods:
                file.write(mod + '\n')
        return user + ' removed as mod.'

    def add_channel(channel):
        channel = channel.lower()
        if channel in channels:
            return None
        channels.append(channel)
        with open(path + 'bot/channels.txt', 'a') as file:
            file.write(channel + '\n')
        return channel + ' added as channel.'

    def remove_channel(channel):
        channel = channel.lower()
        channels.remove(channel)
        with open(path + 'bot/channels.txt', 'w') as file:
            for c in channels:
                file.write(c + '\n')
        return channel + ' removed as channel.'

    @client.event
    def on_ready():
        t.log('Connected as ' + client.user.name + ' (' + client.user.id + ')')

    @client.event
    def on_message(message):
        if message.content[0] == '.' and message.author.name.lower() in mods:
            msg = message.content[1:].split()
            if len(msg) == 2:
                if msg[0] == 'get':
                    if msg[1] == 'whitelist':
                        client.send_message(message.channel, t.get_whitelist_as_string())
                    if msg[1] == 'blacklist':
                        client.send_message(message.channel, t.get_blacklist_as_string())
                    if msg[1] == 'keywords':
                        client.send_message(message.channel, t.get_keywords_as_string())
                    if msg[1] == 'skipwords':
                        client.send_message(message.channel, t.get_skipwords_as_string())
                    if msg[1] == 'live':
                        client.send_message(message.channel, t.get_live_as_string())
                    if msg[1] == 'mods':
                        client.send_message(message.channel, get_mods_as_string())
                    if msg[1] == 'channels':
                        client.send_message(message.channel, get_channels_as_string())
            if len(msg) == 3:
                if msg[0] == 'add':
                    if msg[1] == 'whitelist':
                        client.send_message(message.channel, t.add_whitelist(msg[2]))
                    if msg[1] == 'blacklist':
                        client.send_message(message.channel, t.add_blacklist(msg[2]))
                    if msg[1] == 'keyword':
                        client.send_message(message.channel, t.add_keyword(msg[2]))
                    if msg[1] == 'skipword':
                        client.send_message(message.channel, t.add_skipword(msg[2]))
                    if msg[1] == 'mod':
                        client.send_message(message.channel, add_mod(msg[2]))
                    if msg[1] == 'channel':
                        client.send_message(message.channel, add_channel(msg[2]))
                if msg[0] == 'remove':
                    if msg[1] == 'whitelist':
                        client.send_message(message.channel, t.remove_whitelist(msg[2]))
                    if msg[1] == 'blacklist':
                        client.send_message(message.channel, t.remove_blacklist(msg[2]))
                    if msg[1] == 'keyword':
                        client.send_message(message.channel, t.remove_keyword(msg[2]))
                    if msg[1] == 'skipword':
                        client.send_message(message.channel, t.remove_skipword(msg[2]))
                    if msg[1] == 'mod':
                        client.send_message(message.channel, remove_mod(msg[2]))
                    if msg[1] == 'channel':
                        client.send_message(message.channel, remove_channel(msg[2]))

    def poll_streams():
        time.sleep(5.0)
        t.fetch_livestreams()
        time.sleep(10.0)
        while True:
            msg = t.fetch_livestreams()
            if msg is not None:
                for channel in client.get_all_channels():
                    if channel.name.lower() in channels:
                        client.send_message(channel, msg)
                        t.log(msg)
            time.sleep(30.0)

    live_status = threading.Thread(target=poll_streams, args=())
    discord_client = threading.Thread(target=client.run, args=())
    live_status.start()
    discord_client.start()

if __name__ == "__main__":
    discord_bot()
