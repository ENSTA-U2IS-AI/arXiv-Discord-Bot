# ArXiV Bot

This repository contains a discord bot that allows you to make requests on the arxiv api:
 - It allows you to search the database with a prompt or with a category. The search can be configured.
 - It also automatically sends new papers linked to a category directly to a channel. Settings can be configured.
 - The use of private channels (Direct Messages) is also possible.

## Start

To easily setup a conda environment:
```bash
conda create -n arxiv-bot
conda activate arxiv-bot
conda install pip 
pip install -r requirements.txt
```

You will need to create a file `token.0` at the root which contains your token (secret). 
You must have created a discord [application](https://discord.com/developers/applications) first which gives you access to a bot token. 
More info [here](https://discord.com/developers/docs/intro).

To launch the bot, just use the following command
```bash
python3 main.py
```
