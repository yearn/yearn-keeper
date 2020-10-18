import time
from pathlib import Path

import toml
from brownie import Contract, Wei
from click import secho
from eth_utils import humanize_seconds

db_path = Path("keeper.toml")
uniswap = Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")


class Keeper3Crv:
    address = "0xC59601F0CC49baa266891b7fc63d2D5FE097A79D"

    def __init__(self):
        strategy = Contract(self.address)
        self.vote_proxy = Contract(strategy.voter())
        self.gauge = Contract(strategy.gauge())
        self.curve_pool = Contract(strategy.curve())
        fee_max = strategy.FEE_DENOMINATOR()
        self.keep_crv = strategy.keepCRV() / fee_max
        self.performance_fee = strategy.performanceFee() / fee_max
        self.strategist_reward = strategy.strategistReward() / fee_max
        self.name = strategy.getName()
        self.strategy = strategy

    @property
    def last_harvest(self):
        if db_path.exists():
            data = toml.loads(db_path.read_text())
            return data.get(str(self.address), 0)
        return 0

    def update_last_harvest(self):
        data = toml.loads(db_path.read_text()) if db_path.exists() else {}
        data[self.address] = int(time.time())
        db_path.write_text(toml.dumps(data))

    def time_trigger(self, harvest_interval=86_400):
        condition = time.time() >= self.last_harvest + harvest_interval
        color = "green" if condition else "red"
        secho(f"since last harvest: {humanize_seconds(time.time() - self.last_harvest)}", fg=color)
        return condition

    def earnings_trigger(self, min_output=1000):
        crv_minted = self.gauge.claimable_tokens.call(self.vote_proxy)
        print(f"mint {crv_minted.to('ether')} crv from gauge")
        crv_minted *= 1 - self.keep_crv
        if crv_minted == 0:
            return False

        path = [self.strategy.crv(), self.strategy.weth(), self.strategy.dai()]
        dai_out = uniswap.getAmountsOut(crv_minted, path)[-1]
        output = self.curve_pool.calc_token_amount([dai_out, 0, 0], True)
        color = "green" if output >= min_output else "red"
        secho(f"swap to {output.to('ether')} lp", fg=color)
        print(f"increase {output / self.strategy.balanceOf():+.18%}")
        return output >= min_output

    def gas_cost_trigger(self, gas_price):
        gas_price = Wei(gas_price)
        gas_limit = int(self.strategy.harvest.estimate_gas({"from": self.strategy.strategist()}) * 1.1)

        crv_minted = self.gauge.claimable_tokens.call(self.vote_proxy)
        if crv_minted == 0:
            return False

        crv_minted *= 1 - self.keep_crv
        # this is a bit simplified since strategist will need to convert back to ether to cover the gas costs
        path = [self.strategy.crv(), self.strategy.weth()]
        eth_out = uniswap.getAmountsOut(crv_minted, path)[-1]
        strategist_eth = Wei(eth_out * self.strategist_reward)

        gas_cost = Wei(gas_price * gas_limit)
        print(f"strategist reward: {strategist_eth.to('ether')} eth")
        print(f"gas cost: {gas_cost.to('ether')} ({gas_limit} × {gas_price.to('gwei')} gwei)")
        color = "green" if strategist_eth - gas_cost > 0 else "red"
        secho(f"keeper profit: {(strategist_eth - gas_cost).to('ether')} eth", fg=color)
        return strategist_eth >= gas_cost

    def harvest_trigger(self, gas_price, harvest_interval=86_400, min_earnings=1000):
        secho(f"checking {self.name}", fg='yellow')
        return (
            self.time_trigger(harvest_interval)
            and self.earnings_trigger(min_earnings)
            and self.gas_cost_trigger(gas_price)
        )

    def harvest(self, gas_price, user):
        tx = self.strategy.harvest({"from": user, "gas_price": gas_price})
        output = tx.events["Harvested"]["wantEarned"]
        secho(f"harvested {output.to('ether')} lp", fg="green", bold=True)
        self.update_last_harvest()


keeper_registry = {keeper.address: keeper() for keeper in [Keeper3Crv]}
