# yearn keeper

a keeper bot for yearn v1 strategies which is a tad too smart

## requirements

- python 3.7+
- `pip install eth-brownie`
- `geth --http --graphql`
- being assigned a strategist role

## supported strategies

- `StrategyCurve3CrvVoterProxy` uses a combination of the following
    - 24h min interval
    - 1000 3Crv min gross earnings
    - cover gas costs with strategist reward
