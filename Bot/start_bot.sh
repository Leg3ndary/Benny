#!/bin/bash

tmux kill-session -a -t Bot

tmux rename-session -t Bot DeadBot

tmux new-session -d -s Bot 'python3 Benny/Bot/bot.py'

tmux new-session -d -s Lavalink 'java -jar Benny/Lavalink.jar'

tmux kill-session -t DeadBot