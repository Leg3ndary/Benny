#!/bin/bash

tmux rename-session -t Bot DeadBot

tmux new-session -d -s Bot 'python3 Benny/Bot/bot.py'

tmux kill-session -a -t Bot

tmux new-session -d -s Lavalink 'java -jar Benny/Lavalink.jar'
