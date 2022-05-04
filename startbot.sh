#!/bin/bash

tmux new-session -d -s music -n lavalink
tmux new-session -d -s bot -n benny

tmux send-keys -t music:lavalink "cd/Benny" Enter
tmux send-keys -t music:lavalink "java -jar lavalink.jar" Enter

tmux send-keys -t bot:benny "cd /Benny" Enter
tmux send-keys -t bot:benny "python3 Bot/bot.py" Enter