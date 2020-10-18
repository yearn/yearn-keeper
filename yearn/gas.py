import requests


def gas_price_geth(position=500):
    query = "{ pending { transactions { gasPrice }}}"
    resp = requests.post("http://127.0.0.1:8545/graphql", json={"query": query})
    data = resp.json()["data"]["pending"]["transactions"]
    prices = [int(x["gasPrice"], 16) for x in data]
    return sorted(prices, reverse=True)[:position][-1]
