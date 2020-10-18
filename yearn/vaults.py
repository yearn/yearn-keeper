from dataclasses import dataclass
from typing import Union

from brownie import Contract, interface, web3
from brownie.network.contract import InterfaceContainer


@dataclass
class Vault:
    vault: Union[str, InterfaceContainer]
    controller: Union[str, InterfaceContainer]
    token: Union[str, interface.ERC20]
    strategy: str
    is_wrapped: bool
    is_delegated: bool

    def __post_init__(self):
        self.vault = Contract(self.vault)
        self.controller = Contract(self.controller)
        self.strategy = Contract(self.strategy)
        self.token = interface.ERC20(self.token)


def load_vaults(registry):
    return [Vault(*params) for params in zip(registry.getVaults(), *registry.getVaultsInfo())]


def load_registry():
    return Contract(web3.ens.resolve("registry.ychad.eth"))
