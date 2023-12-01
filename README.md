# Telegram Bot for GhostMarket activities

## How to install?
- Create a Python environment with dependencies  from `requirements.txt` 
- Build a Docker image using the `Dockerfile` in this repo

## Configuration
### Mandatory
You need to add environment variables in order to be able to run the bot:
- The Discord channel ID you want the bot to post in. Variable should be named `CHANNEL_ID`
- The Token for the bot you want to use. If you need help to create a Telegram bot you should DM `@Botfather` on Telegram. Variable should be named `BOT_TOKEN`
### Filtering options
You can use this bot only for a specific chain or a specific collection by modifying .
For a chain use one of those options on `CHAIN_FILTER` environment variable:
* "pha": "Phantasma",  
* "bsc": "BSC",  
* "n3": "N3",  
* "polygon": "Polygon",  
* "avalanche": "Avalanche",  
* "eth": "Ethereum",  
* "base": "Base"

For a collection use the slug of your collection (you can see It on the URL when visiting the collection on GhostMarket: for example `bored-doge` for DogeRift NFTS https://ghostmarket.io/collection/bored-doge/) on `COLLECTION_FILTER`.

## How to run?
For launching the bot either you run the Docker image (see `docker-compose.yml`example) or the Python script
