# gitea install in a multiuser env

not everybody wants a root vps, where things can go wrong badly. this repos show a way to 
install gitea in a shared (hosting) environment.

- app.ini with basic config you would normall use when installed on a shared environment
- very reduced systemd example, run it as systemctl --user
- fabfile.org for deployment (totally optional), take care, badly adopted from my django projects. needs fabric<2
