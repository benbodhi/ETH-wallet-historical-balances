# This script retrieves and calculates Ethereum and ERC20 token balances for specified wallet addresses
# at certain block numbers. The USD value for the tokens is determined using the CryptoCompare API.
# Editable settings are read from a .env file for API keys and from config.yaml for configuration settings.

import requests
import csv
from time import sleep
from datetime import datetime
import os
from dotenv import load_dotenv
import yaml

# Load .env file to populate environment variables with API keys
load_dotenv()

# API Endpoints and keys
ETHERSCAN_API_ENDPOINT = "https://api.etherscan.io/api"
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
INFURA_API_ENDPOINT = "https://mainnet.infura.io/v3/"
INFURA_API_KEY = os.getenv('INFURA_API_KEY')
CRYPTOCOMPARE_API_ENDPOINT = "https://min-api.cryptocompare.com/data/v2/histoday"
CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY')

# Load settings from config.yaml
with open("config.yaml", 'r') as stream:
    try:
        yaml_data = yaml.safe_load(stream)
        WALLET_ADDRESSES = yaml_data.get('WALLET_ADDRESSES', [])
        print(f"Loaded addresses: {WALLET_ADDRESSES}")  # Debug print
        BLOCK_NUMBERS = [str(num) for num in yaml_data.get('BLOCK_NUMBERS', [])]
        EXCLUDE_TOKEN_CONTRACTS = yaml_data.get('EXCLUDE_TOKEN_CONTRACTS', [])
        RATE_LIMIT_DELAY = yaml_data.get('RATE_LIMIT_DELAY', 0.2)
    except yaml.YAMLError as exc:
        print(exc)

def block_to_date(block_number):
    """Convert Ethereum block number to date using Etherscan."""
    # API parameters to retrieve block details
    params = {
        "module": "block",
        "action": "getblockreward",
        "blockno": block_number,
        "apikey": ETHERSCAN_API_KEY
    }
    # API request to Etherscan
    response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    # Extract timestamp and convert to a human-readable date
    timestamp = response.json().get('result', {}).get('timeStamp', 0)
    return datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d')

def get_eth_balance(address, block_number):
    """Fetch the ETH balance for an address at a specific block using Infura."""
    url = f"{INFURA_API_ENDPOINT}{INFURA_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    # JSON-RPC request format to retrieve ETH balance
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBalance",
        "params": [address, hex(int(block_number))]
    }
    # API request to Infura
    response = requests.post(url, headers=headers, json=data)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    # Extract the balance and convert from Wei to ETH
    result = response.json().get('result')
    if result:
        return int(result, 16) / 10**18
    else:
        print(f"Error fetching ETH balance at block {block_number} for address {address}.")
        return 0

def get_erc20_tokens(address):
    """Fetch the list of ERC20 tokens associated with an address using Etherscan."""
    # API parameters to retrieve ERC20 token transactions
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    # API request to Etherscan
    response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    # Extract tokens associated with the address
    tokens = {}
    if response.status_code == 200:
        transactions = response.json().get('result', [])
        for tx in transactions:
            tokens[tx['contractAddress']] = tx['tokenSymbol']
    return tokens

def reconstruct_erc20_balance(address, contract, symbol, block_number):
    """Reconstruct the ERC20 token balance for an address at a specific block."""
    # Start by fetching the current balance of the token
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": contract,
        "address": address,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }
    # API request to Etherscan
    response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    # Extract the current balance
    current_balance = int(response.json().get('result', '0'))

    # Fetch all token transfers up to the desired block number
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": block_number,
        "sort": "desc",  # latest first
        "apikey": ETHERSCAN_API_KEY
    }
    # API request to Etherscan for token transfers
    response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    token_transfers = response.json().get('result', [])

    # Fetch all internal transactions up to the desired block number
    params = {
        "module": "account",
        "action": "txlistinternal",
        "address": address,
        "startblock": 0,
        "endblock": block_number,
        "sort": "desc",  # latest first
        "apikey": ETHERSCAN_API_KEY
    }
    # API request to Etherscan for internal transactions
    response = requests.get(ETHERSCAN_API_ENDPOINT, params=params)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)
    internal_transfers = response.json().get('result', [])

    # Reconstruct balance by processing token and internal transactions
    for tx in token_transfers:
        if tx['tokenSymbol'] == symbol:
            if tx['to'] == address.lower():
                current_balance -= int(tx['value'])
            elif tx['from'] == address.lower():
                current_balance += int(tx['value'])

    for tx in internal_transfers:
        if 'contractAddress' in tx and tx['contractAddress'] == contract:
            if tx['type'] == "call":
                if tx['to'] == address.lower():
                    current_balance -= int(tx['value'])
                elif tx['from'] == address.lower():
                    current_balance += int(tx['value'])

    return current_balance / 10**18  # Convert from wei to token decimals

def get_token_price_on_date_cryptocompare(token_symbol, date):
    """Get token price on a specific date using CryptoCompare API."""
    # Convert date to timestamp
    dt = datetime.strptime(date, "%Y-%m-%d")
    timestamp = int(dt.timestamp())

    # Form the API URL to fetch the historical price
    url = f"{CRYPTOCOMPARE_API_ENDPOINT}?fsym={token_symbol}&tsym=USD&limit=1&toTs={timestamp}"

    headers = {
        "Authorization": f"Apikey {CRYPTOCOMPARE_API_KEY}"
    }

    # API request to CryptoCompare
    response = requests.get(url, headers=headers)
    # Delay to respect the rate limit
    sleep(RATE_LIMIT_DELAY)

    if response.status_code == 200:
        data = response.json().get('Data', {}).get('Data', [])
        if data:
            return data[0].get('close')
    print(f"Error fetching price for {token_symbol} on {date} from CryptoCompare.")
    return None

def main():
    """Main function that orchestrates the process of fetching balances and writing them to a CSV."""
    with open('balances.csv', 'w', newline='') as csvfile:
        # Define the CSV columns
        fieldnames = ['Address', 'Block Number', 'Balance', 'Token Ticker/Name', 'Token Contract', 'USD Value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for address in WALLET_ADDRESSES:
            print(f"Processing address: {address}")
            for block_number in BLOCK_NUMBERS:
                date = block_to_date(block_number)

                # Fetch and write ETH balances
                print(f"  Fetching ETH balance for block {block_number}...")
                eth_balance = get_eth_balance(address, block_number)

                # Fetch the price of ETH for the date
                eth_usd_price = get_token_price_on_date_cryptocompare("ETH", date)

                # If we couldn't fetch the ETH price, set it to 0
                if not eth_usd_price:
                    eth_usd_price = 0

                eth_usd_value = eth_balance * eth_usd_price

                writer.writerow({
                    'Address': address,
                    'Block Number': block_number,
                    'Balance': eth_balance,
                    'Token Ticker/Name': 'ETH',
                    'Token Contract': 'ETH',
                    'USD Value': eth_usd_value
                })

                # Fetch and write ERC20 balances
                erc20_tokens = get_erc20_tokens(address)
                for contract, symbol in erc20_tokens.items():
                    if contract in EXCLUDE_TOKEN_CONTRACTS:
                        print(f"Skipping spam tokens: {symbol}")
                        continue  # Skip excluded tokens
                    print(f"  Reconstructing {symbol} balance for block {block_number}...")
                    reconstructed_balance = reconstruct_erc20_balance(address, contract, symbol, block_number)
                    # Fetch the price directly using CryptoCompare
                    usd_price = get_token_price_on_date_cryptocompare(symbol, date)

                    # If we couldn't fetch the price, set it to None
                    if not usd_price:
                        usd_price = 0

                    usd_value = reconstructed_balance * usd_price

                    # Only add non-zero balances to CSV
                    if reconstructed_balance > 0:
                        writer.writerow({
                            'Address': address,
                            'Block Number': block_number,
                            'Balance': reconstructed_balance,
                            'Token Ticker/Name': symbol,
                            'Token Contract': contract,
                            'USD Value': usd_value
                        })

    print("Completed processing all addresses. Check balances.csv for results.")

if __name__ == "__main__":
    main()