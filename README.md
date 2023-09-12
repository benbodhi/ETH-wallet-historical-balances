# Ethereum Wallet Balances Extractor

This tool allows you to fetch and calculate ETH and ERC20 token balances for a list of Ethereum addresses at specific block numbers. The balances, along with their USD values at the corresponding dates, are exported to a `balances.csv` file.

## Features

- Retrieves ETH and ERC20 token balances at specific block numbers without the need for a premium API.
- Calculates the USD value of tokens using the CryptoCompare API.
- Exports results to a CSV file.

## Prerequisites

1. **Python**: Ensure you have Python 3.x installed.
2. **Pip**: The Python package installer.

## Setup

### 1. Clone or Download the Repository

If you're familiar with Git, clone the repository. Otherwise, simply download the Python script and save it to a directory on your computer.

### 2. Install Required Python Packages

Navigate to the directory containing the script and run:

```bash
pip install requests python-dotenv pyyaml
```

### 3. Obtain API Keys

Before using the script, you need to obtain API keys from the following platforms:

- [Etherscan](https://etherscan.io/apis)
- [Infura](https://infura.io/)
- [CryptoCompare](https://min-api.cryptocompare.com/)

### 4. Configure API Keys and Settings

- Create a `.env` file in the same directory as your script. Add your API keys as shown below:

```env
ETHERSCAN_API_KEY=your_etherscan_api_key
INFURA_API_KEY=your_infura_api_key
CRYPTOCOMPARE_API_KEY=your_cryptocompare_api_key
```

Replace placeholders (e.g., `your_etherscan_api_key`) with your actual API keys.

- Configure settings using the `config.yaml` file. A sample `config.yaml` is available in the repository. Edit it to specify your wallet addresses, block numbers, and any spam token contracts you want to exclude. Also, set the desired rate limit delay.

### 5. Run the Script

Navigate to the directory containing your script in your terminal or command prompt. Run the script using:

```bash
python run.py
```

### 6. Check Results

After the script has successfully run, you'll find a `balances.csv` file in the same directory. This file contains the extracted balances and their USD values.

## Disclaimer

This script is provided as-is without any guarantees. Always ensure you double-check any financial data and adhere to the rate limits of the APIs you are using.

## License

This script is open-source and free to use. There's no associated license. Do what you want, but please use responsibly.
