tmux kill-session -t Lavalink || echo Lavalink Session Not Found
tmux kill-session -t Bennybot || echo BennyBot Session Not found
tmux new-session -d -s "Lavalink" /Benny/scripts/start_lavalink.sh
tmux new-session -d -s "BennyBot" /Benny/scripts/start_bot.sh