import os

import requests
from brownie import Wei

ETH_RPC_URL = os.environ.get("ETH_RPC_URL") or "http://127.0.0.1:8545"


def gas_price_geth(position=500):
    query = "{ pending { transactions { gasPrice }}}"
    resp = requests.post(f"{ETH_RPC_URL}/graphql", json={"query": query})
    data = resp.json()["data"]["pending"]["transactions"]
    prices = [int(x["gasPrice"], 16) for x in data]
    return Wei(sorted(prices, reverse=True)[:position][-1])
