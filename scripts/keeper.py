import time
import warnings

from brownie import accounts, chain
from brownie.network.contract import BrownieEnvironmentWarning
from click import secho
from yearn.gas import gas_price_geth
from yearn.keepers import keeper_registry
from yearn.vaults import load_registry, load_vaults

warnings.filterwarnings("ignore", category=BrownieEnvironmentWarning)


def main():
    user = accounts.load(input("brownie account: "))
    print(f"loaded keeper account: {user}")

    registry = load_registry()
    vaults = load_vaults(registry)
    secho(f"loaded {len(vaults)} vaults", fg="yellow")

    keepers = [
        keeper_registry[str(vault.strategy)]
        for vault in vaults
        if hasattr(vault.strategy, "strategist")
        and vault.strategy.strategist() == user
        and str(vault.strategy) in keeper_registry
    ]
    if not keepers:
        secho("nothing to keep, exiting", fg="yellow")
        return

    secho(f"keeping {len(keepers)} vaults", fg="green")

    for block in chain.new_blocks():
        for keeper in keepers:
            secho(f">>> {block.number}", dim=True)
            gas_price = gas_price_geth()
            secho(f"gas price: {gas_price.to('gwei')} gwei")
            if keeper.harvest_trigger(gas_price):
                keeper.harvest(gas_price, user)
        
        time.sleep(600)
