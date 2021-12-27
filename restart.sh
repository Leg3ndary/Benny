cd

tmux kill-session -t bot
tmux kill-session -t music

tmux new-session -d -s bot "bash Benny/Benny/scripts/sb.sh"
tmux new-session -d -s music "bash Benny/Benny/scripts/sl.sh"

echo Finished