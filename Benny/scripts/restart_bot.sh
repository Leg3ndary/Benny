tmux kill-session -t Lavalink
tmux kill-session -t Bennybot
tmux new-session -d -s "Lavalink" /Benny/scripts/start_lavalink.sh
tmux new-session -d -s "BennyBot" /Benny/scripts/start_bot.sh