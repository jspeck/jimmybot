#!/usr/bin/env python3
import discord
import requests
import re
import threading
import time

def main():
    email = ""
    pw = ""
    client = discord.Client()
    client.login(email, pw)
    main_channel = "streams"
    stream_list = [line.rstrip('\n').lower() for line in open('streams.txt')]
    keywords = [line.rstrip('\n').lower() for line in open('keywords.txt')]

    def poll_livestreams(oldlive=[]):
        print("entered poll")
        newlive = []
        temp = []
        ret = []
        r = requests.get("https://api.twitch.tv/kraken/streams?game=Super%20Mario%2064").json()
        for stream in r['streams']:
            if stream['channel']['display_name'].lower() not in stream_list:
                has_keyword = False
                for keyword in keywords:
                    if keyword in stream['channel']['status']:
                        has_keyword = True
                if has_keyword == False:
                    continue
            newlive.append(stream['channel']['display_name'])
            if stream['channel']['display_name'] not in oldlive:
                oldlive.append(stream['channel']['display_name'])
                status = stream['channel']['status']
                for link in re.findall(r'(https?://[^\s]+)', status):
                    status = status.replace(link, "`"+link+"`")
                temp.append("NOW LIVE : `" + stream['channel']['url'] + "` | ")
                temp.append(status + " ")
                #temp.append("[Viewers: " + str(stream['viewers']) + "]")
                ret.append(" ".join(temp))
                del temp[:]

        for stream in list(oldlive):
            if stream not in newlive:
                oldlive.remove(stream)
        if not ret:
            return None
        return "\n".join(ret)

    @client.event
    def on_ready():
	    print('Connected!')
	    print('Username: ' + client.user.name)
	    print('ID: ' + client.user.id)

    @client.event
    def on_message(message):
        if message.content[0] == ".":
            msg = message.content[1:].split(" ")
            if len(msg) == 3:
                if msg[0] == "add":
                    if msg[1] == "stream":
                        stream_list.append(msg[2])
                        with open('streams.txt', 'a') as file:
                            file.write(msg[2] + "\n")
                        client.send_message(message.channel, "Added stream {}.".format(msg[2]))
                    if msg[1] == "keyword":
                        keywords.append(msg[2])
                        with open('keywords.txt', 'a') as file:
                            file.write(msg[2] + "\n")
                        client.send_message(message.channel, "Added keyword {}.".format(msg[2]))

    def post_livestreams():
        time.sleep(5.0)
        while True:
            msg = poll_livestreams()
            if msg is not None:
                '''
                for member in client.get_all_members():
                    if member.name == "bit":
                        client.send_message(member, msg)
                '''
                for channel in client.get_all_channels():
                    if channel.name == main_channel:
                        client.send_message(channel, msg)
            time.sleep(30.0)

    livestatus = threading.Thread(target=post_livestreams, args=())
    discord_client = threading.Thread(target=client.run, args=())
    livestatus.start()
    discord_client.start()

if __name__ == "__main__":
    main()
