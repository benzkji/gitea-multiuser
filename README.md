# gitea install in a multiuser env

not everybody wants a root vps, where things can go wrong badly. this repos show a way to 
install gitea in a shared (hosting) environment.

- app.ini with basic config you would normall use when installed on a shared environment
- runs behind an nginx proxy (not included :)
- no SSL, this is done on nginx/proxy level
- very reduced systemd example, run it as systemctl --user
- fabfile.org for deployment (totally optional), take care, badly adopted from my django projects. needs fabric<2


### fair warnings

- you'll probably not be able to run ssh on port 22
- make a backup ;-)
