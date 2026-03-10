import sys

import ruamel.yaml as yaml
from web3.auto import w3

w3.eth.account.enable_unaudited_hdwallet_features()

testnet_config_path = "genesis-config.yaml"
if len(sys.argv) > 1:
    testnet_config_path = sys.argv[1]

with open(testnet_config_path) as stream:
    data = yaml.safe_load(stream)

for key, _value in data["el_premine"].items():
    acct = w3.eth.account.from_mnemonic(data["mnemonic"], account_path=key, passphrase="")
    print(f"{key},{acct.address},{acct.key.hex()}")
