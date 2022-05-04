#!/bin/bash

tmux new-session -d -s bot
echo "Starting bot session"
tmux new-session -d -s lavalink
echo "Starting lavalink session"

tmux send-keys -t lavalink "cd/Benny" Enter
tmux send-keys -t lavalink "java -jar lavalink.jar" Enter
echo "Starting lavalink.jar"

sleep 3

tmux send-keys -t bot "cd /Benny" Enter
tmux send-keys -t bot "python3 Bot/bot.py" Enter
echo "Starting bot.py"