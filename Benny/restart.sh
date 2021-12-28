cd

tmux kill-session -t bot
echo Killed Bot
tmux kill-session -t music
echo Killed Music


tmux new-session -d -s music "bash Benny/Benny/scripts/sl.sh"
echo Loaded music

tmux new-session -d -s bot "bash Benny/Benny/scripts/sb.sh"
echo Loaded bot

echo Finished