#!/bin/bash

tmux new-session -d -s bot
tmux new-session -d -s lavalink

tmux send-keys -t lavalink "cd/Benny" Enter
tmux send-keys -t lavalink "java -jar lavalink.jar" Enter

tmux send-keys -t bot "cd /Benny" Enter
tmux send-keys -t bot "python3 Bot/bot.py" Enter