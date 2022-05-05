#!/bin/bash

echo "Trying to kill previous sessions."
{
    tmux kill-session -t bot && echo "Killed bot session"
} || {
    echo "No bot session found"
}
{
    tmux kill-session -t lavalink && echo "Killed lavalink session"
} || {
    echo "No lavalink session found"
}

bash start.sh
echo "Successfully started bot"