import asyncio
import logging
import os
import requests
import time
import urllib3

from typing import NoReturn

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import Bot


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

urllib3.disable_warnings()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
CHAIN_FILTER = os.environ.get("CHAIN_FILTER", "")
COLLECTION_FILTER = os.environ.get("COLLECTION_FILTER", "")
GM_SALES_URL = "https://api.ghostmarket.io/api/v2/events?page=1&size=100&DateFrom={}&DateTill={}&orderBy=date&orderDirection=desc&getTotal=true&localCurrency=USD&chain=&grouping=true&eventKind=orderfilled&onlyVerified=false&showBurned=false&nftName=&showBlacklisted=false&showNsfw=false&chain={}&collection={}&platforms[]=ghostmarket"
GM_OFFERS_URL = "https://api.ghostmarket.io/api/v2/events?page=1&size=100&DateFrom={}&DateTill={}&orderBy=date&orderDirection=desc&getTotal=true&localCurrency=USD&chain=&grouping=true&eventKind=offercreated&onlyVerified=false&showBurned=false&nftName=&showBlacklisted=false&showNsfw=false&chain={}&collection={}&platforms[]=ghostmarket"
GM_BIDS_URL = "https://api.ghostmarket.io/api/v2/events?page=1&size=100&DateFrom={}&DateTill={}&orderBy=date&orderDirection=desc&getTotal=true&localCurrency=USD&chain=&grouping=true&eventKind=orderbid&onlyVerified=false&showBurned=false&nftName=&showBlacklisted=false&showNsfw=false&chain={}&collection={}&platforms[]=ghostmarket"
GM_LISTINGS_URL = "https://api.ghostmarket.io/api/v2/events?page=1&size=100&DateFrom={}&DateTill={}&orderBy=date&orderDirection=desc&getTotal=true&localCurrency=USD&chain=&grouping=true&eventKind=ordercreated&onlyVerified=false&showBurned=false&nftName=&showBlacklisted=false&showNsfw=false&chain={}&collection={}&platforms[]=ghostmarket"
GM_ASSETS_URL = "https://api.ghostmarket.io/api/v2/assets?Chain={}&Contract={}&TokenIds[]={}"
GM_ATTR_URL = "https://api.ghostmarket.io/api/v2/asset/{}/attributes?page=1&size={}"
CHAIN_MAPPING = {
    "pha": "Phantasma",
    "bsc": "BSC",
    "n3": "N3",
    "polygon": "Polygon",
    "avalanche": "Avalanche",
    "eth": "Ethereum",
    "base": "Base"
}
DECIMALS_MAPPING = {
    "BNB": 18,
    "WBNB": 18,
    "MATIC": 18,
    "WMATIC": 18,
    "BUSD": 18,
    "SOUL": 8,
    "GAS": 8,
    "KCAL": 10,
    "GOATI": 3,
    "ETH": 18,
    "WETH": 18,
    "NEO": 0,
    "DYT": 18,
    "DANK": 18,
    "USDC": 6,
    "SWTH": 8,
    "CAKE": 18,
    "DAI": 18,
    "BNEO": 8,
    "AVAX": 18,
    "WAVAX": 18,
    "FLM": 8,
    "GM": 8,
    "O3": 18,
    "NUDES": 8,
    "APE": 18,
    "SOM": 8,
    "FUSDT": 6,
    "FUSD": 8,
    "NEX": 8,
    "NEP": 8
}
ATTRIBUTES_TO_SHOW = 6


def _get_asset_id(chain, contract, token_id):
    url = GM_ASSETS_URL.format(chain, contract, token_id)
    res = requests.get(url, verify=False).json()
    return res["assets"][0]["nftId"]


def _get_asset_attributes(asset_id):
    url = GM_ATTR_URL.format(asset_id, ATTRIBUTES_TO_SHOW)
    res = requests.get(url, verify=False).json()
    attributes = res.get("attributes", []) if res.get("attributes") else []
    attributes = [x for x in attributes if x['key'].get('displayName')]
    return attributes


def get_gm_events_from_last_time(base_url, last_time, event_name, action_name, events, cursor):
    max_time_to_get = int(time.time()) - 60
    if max_time_to_get <= last_time:
        return events, last_time
    url = base_url.format(last_time, max_time_to_get, CHAIN_FILTER, COLLECTION_FILTER)
    if cursor:
        url += f"Cursor={cursor}"
    res = requests.get(url, verify=False).json()
    for i, event in enumerate(res.get("events", []) if res.get("events", []) else []):
        if i == 0:
            last_time = event['date'] + 1
        chain = event['contract']['chain']
        chain_name = CHAIN_MAPPING.get(chain, chain)
        collection = event['collection']['name']
        collection_slug = event['collection']['slug']
        if event_name == "sale":
            user = event['toAddress'].get('offchainTitle', event['toAddress'].get('offchainName', event['toAddress'].get('onchainName', event['toAddress']['address'])))
            if len(user) > 20 and user == event['toAddress']['address']:
                user = f"{user[:5]}...{user[-5:]}"
        else:
            user = event['fromAddress'].get('offchainTitle', event['fromAddress'].get('offchainName', event['fromAddress'].get('onchainName', event['fromAddress']['address'])))
            if len(user) > 20 and user == event['fromAddress']['address']:
                user = f"{user[:5]}...{user[-5:]}"
        currency = event['quoteContract']['symbol']
        decimals = DECIMALS_MAPPING.get(currency, 0)
        price = f"{round(int(event['price']) / 10 ** decimals, 4)}"
        price = price[:-2] if price[-2:] == ".0" else price
        price_usd = round(float(event['localPrice']), 2)
        contract = event['contract']['hash']
        if event.get('metadata') is not None:
            token_id = event['tokenId']
            nft_name = event['metadata']['name']
            nft_url = f"https://ghostmarket.io/asset/{chain}/{contract}/{token_id}/"
            mint_num = event['metadata']['mintNumber']
            mint_max = event['series']['maxSupply']
            asset_id = _get_asset_id(chain, contract, token_id)
            attributes = _get_asset_attributes(asset_id)
            if attributes:
                if chain == "pha":
                    mint_part = f"{mint_num} of {mint_max}" if str(mint_max) != '0' else f"{mint_num}"
                    description = f'<a href="{nft_url}">{nft_name}</a>\n{action_name} by <b>{user}</b>\nFor <b>{price} {currency}</b> (${price_usd})\nMint <b>{mint_part}</b>\n\n'
                else:
                    description = f'<a href="{nft_url}">{nft_name}</a>\n{action_name} by <b>{user}</b>\nFor <b>{price} {currency}</b> (${price_usd})\n\n'
            else:
                attributes = []
                if chain == "pha":
                    mint_part = f"{mint_num} of {mint_max}" if str(mint_max) != '0' else f"{mint_num}"
                    description = f'<a href="{nft_url}">{nft_name}</a>\n{action_name} by <b>{user}</b>\nFor <b>{price} {currency}</b> (${price_usd})\nMint <b>{mint_part}</b>'
                else:
                    description = f'<a href="{nft_url}">{nft_name}</a>\n{action_name} by <b>{user}</b>\nFor <b>{price} {currency}</b> (${price_usd})'
        else:
            nft_name = "Collection offer"
            nft_url = f"https://ghostmarket.io/collection/{collection_slug}/"
            description = f'<a href="{nft_url}">{nft_name}</a>\n{action_name} by <b>{user}</b>\nFor <b>{price} {currency}</b> (${price_usd})'

        message = f"<b>New {event_name}: {chain_name} {collection} NFT</b>\n{description}"

        if event.get('metadata') is not None:
            for attr in attributes:
                message = f'{message}<b>{attr["key"]["displayName"]}:</b> {attr["value"]["value"]}\n'
        events.append(message)
    if res.get("next"):
        return get_gm_events_from_last_time(base_url, last_time, event_name, action_name, events, res.get("next"))
    return events, last_time


async def main() -> NoReturn:
    """Run the bot."""
    # Here we use the `async with` syntax to properly initialize and shutdown resources.
    async with Bot(BOT_TOKEN) as bot:
        last_sales_time = int(time.time())
        last_bids_time = int(time.time())
        last_offers_time = int(time.time())
        last_listings_time = int(time.time())
        while True:
            try:
                sales, last_sales_time = get_gm_events_from_last_time(GM_SALES_URL, last_sales_time, "sale", "Bought",
                                                                      [], None)
                for sale in sales[::-1]:
                    await bot.send_message(CHANNEL_ID, sale, parse_mode="HTML", write_timeout=100, read_timeout=100, connect_timeout=100, pool_timeout=100)
            except:
                last_sales_time = int(time.time())
                print("Error retrieving last sales")
            try:
                listings, last_listings_time = get_gm_events_from_last_time(GM_LISTINGS_URL, last_listings_time,
                                                                            "listing", "Offered", [], None)
                for listing in listings[::-1]:
                    await bot.send_message(CHANNEL_ID, listing, parse_mode="HTML", write_timeout=100, read_timeout=100, connect_timeout=100, pool_timeout=100)
            except:
                last_listings_time = int(time.time())
                print("Error retrieving last listings")
            try:
                offers, last_offers_time = get_gm_events_from_last_time(GM_OFFERS_URL, last_offers_time, "offer",
                                                                        "Offer", [], None)
                for offer in offers[::-1]:
                    await bot.send_message(CHANNEL_ID, offer, parse_mode="HTML", write_timeout=100, read_timeout=100, connect_timeout=100, pool_timeout=100)
            except:
                last_offers_time = int(time.time())
                print("Error retrieving last offers")
            try:
                bids, last_bids_time = get_gm_events_from_last_time(GM_BIDS_URL, last_bids_time, "bid", "Bid", [], None)
                for bid in bids[::-1]:
                    await bot.send_message(CHANNEL_ID, bid, parse_mode="HTML", write_timeout=100, read_timeout=100, connect_timeout=100, pool_timeout=100)
            except:
                last_bids_time = int(time.time())
                print("Error retrieving last bids")
            time.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # Ignore exception when Ctrl-C is pressed
        pass
