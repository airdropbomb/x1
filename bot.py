import asyncio
import aiohttp
import random
import json
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Any
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from colorama import init, Fore, Style
from pyfiglet import Figlet
from art import text2art
import itertools
import re
import requests
from fake_useragent import UserAgent

# Colorama initialization
init(autoreset=True)

class Logger:
    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def info(msg, options=None):
        if options is None:
            options = {}
        timestamp = Logger._get_timestamp()
        emoji = options.get('emoji', 'ℹ️  ')
        context = f"[{options.get('context', '')}] " if options.get('context') else ""
        level = f"{Fore.GREEN}INFO{Style.RESET_ALL}"
        formatted_msg = f"[ {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} ] {emoji}{level} {Fore.WHITE}{context.ljust(20)}{Style.RESET_ALL}{Fore.WHITE}{msg}{Style.RESET_ALL}"
        print(formatted_msg)

    @staticmethod
    def warn(msg, options=None):
        if options is None:
            options = {}
        timestamp = Logger._get_timestamp()
        emoji = options.get('emoji', '⚠️ ')
        context = f"[{options.get('context', '')}] " if options.get('context') else ""
        level = f"{Fore.YELLOW}WARN{Style.RESET_ALL}"
        formatted_msg = f"[ {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} ] {emoji}{level} {Fore.WHITE}{context.ljust(20)}{Style.RESET_ALL}{Fore.WHITE}{msg}{Style.RESET_ALL}"
        print(formatted_msg)

    @staticmethod
    def error(msg, options=None):
        if options is None:
            options = {}
        timestamp = Logger._get_timestamp()
        emoji = options.get('emoji', '❌ ')
        context = f"[{options.get('context', '')}] " if options.get('context') else ""
        level = f"{Fore.RED}ERROR{Style.RESET_ALL}"
        formatted_msg = f"[ {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} ] {emoji}{level} {Fore.WHITE}{context.ljust(20)}{Style.RESET_ALL}{Fore.WHITE}{msg}{Style.RESET_ALL}"
        print(formatted_msg)

    @staticmethod
    def debug(msg, options=None):
        if options is None:
            options = {}
        timestamp = Logger._get_timestamp()
        emoji = options.get('emoji', '🔍  ')
        context = f"[{options.get('context', '')}] " if options.get('context') else ""
        level = f"{Fore.BLUE}DEBUG{Style.RESET_ALL}"
        formatted_msg = f"[ {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} ] {emoji}{level} {Fore.WHITE}{context.ljust(20)}{Style.RESET_ALL}{Fore.WHITE}{msg}{Style.RESET_ALL}"
        print(formatted_msg)

def delay(seconds):
    """Asynchronous delay function"""
    return asyncio.sleep(seconds)

async def countdown(seconds, message):
    """Display countdown timer"""
    for remaining in range(seconds, 0, -1):
        print(f"\r{message} {remaining}s remaining...", end="", flush=True)
        await asyncio.sleep(1)
    print("\r" + " " * 50 + "\r", end="", flush=True)

def center_text(text, width):
    """Center text with ANSI color codes stripped"""
    clean_text = re.sub(r'\x1B\[[0-9;]*[mK]', '', text)
    text_length = len(clean_text)
    total_padding = max(0, width - text_length)
    left_padding = total_padding // 2
    right_padding = total_padding - left_padding
    return " " * left_padding + text + " " * right_padding

def print_header(title):
    """Print header with border"""
    width = 80
    print(f"{Fore.CYAN}┬{'─' * (width - 2)}┬{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│ {title.ljust(width - 4)} │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}┴{'─' * (width - 2)}┴{Style.RESET_ALL}")

def print_info(label, value, context):
    """Print formatted information"""
    Logger.info(f"{label.ljust(15)}: {Fore.CYAN}{value}{Style.RESET_ALL}", 
                {"emoji": "📍 ", "context": context})

def print_profile_info(address, points, rank, balance, context):
    """Print profile information"""
    print_header(f"Profile Info {context}")
    print_info('Wallet Address', mask_address(address), context)
    print_info('Total Points', str(points), context)
    print_info('Rank', str(rank), context)
    print_info('X1T Balance', str(balance), context)
    print("\n")

def mask_address(address):
    """Mask wallet address for display"""
    if not address:
        return 'N/A'
    return f"{address[:6]}{'*' * 6}{address[-6:]}"

class X1EcoChainBot:
    def __init__(self):
        self.user_agent = UserAgent()
        self.global_use_proxy = False
        self.global_proxies = []
        self.session = None
        
    def get_random_user_agent(self):
        """Get random user agent"""
        return self.user_agent.random

    def get_session_headers(self, token=None):
        """Get HTTP session headers"""
        headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,id;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://testnet.x1ecochain.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://testnet.x1ecochain.com/',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': self.get_random_user_agent()
        }
        
        if token:
            headers['authorization'] = token
            
        return headers

    async def request_with_retry(self, method, url, payload=None, headers=None, 
                                 retries=3, backoff=2, context=""):
        """Make HTTP request with retry logic"""
        for i in range(retries):
            try:
                if method.lower() == 'get':
                    response = await self.session.get(url, headers=headers, json=payload)
                elif method.lower() == 'post':
                    response = await self.session.post(url, headers=headers, json=payload)
                else:
                    raise ValueError(f"Method {method} not supported")
                
                return response
                
            except Exception as error:
                error_msg = str(error)
                Logger.error(f"Request failed: {error_msg}", {"context": context})
                
                if i < retries - 1:
                    Logger.warn(f"Retrying {method.upper()} {url} ({i+1}/{retries})", 
                               {"emoji": "🔄", "context": context})
                    await delay(backoff)
                    backoff *= 1.5
                    continue
                    
                raise error

    async def read_accounts(self):
        """Read accounts from pk.txt file"""
        try:
            with open('pk.txt', 'r', encoding='utf-8') as f:
                private_keys = [line.strip() for line in f if line.strip()]
                
            accounts = [{"privateKey": pk} for pk in private_keys]
            
            if not accounts:
                raise ValueError("No private keys found in pk.txt")
                
            Logger.info(f"Loaded {len(accounts)} account{'s' if len(accounts) != 1 else ''}", 
                       {"emoji": "🔑 "})
            return accounts
            
        except Exception as error:
            Logger.error(f"Failed to read pk.txt: {error}", {"emoji": "❌ "})
            return []

    async def read_proxies(self):
        """Read proxies from proxy.txt file"""
        try:
            with open('proxy.txt', 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
                
            if not proxies:
                Logger.warn('No proxies found. Proceeding without proxy.', {"emoji": "⚠️ "})
            else:
                Logger.info(f"Loaded {len(proxies)} prox{'y' if len(proxies) == 1 else 'ies'}", 
                           {"emoji": "🌐 "})
            return proxies
            
        except Exception as error:
            Logger.warn('proxy.txt not found.', {"emoji": "⚠️ "})
            return []

    def derive_wallet_address(self, private_key):
        """Derive wallet address from private key"""
        try:
            account = Account.from_key(private_key)
            return account.address
        except Exception as error:
            Logger.error(f"Failed to derive address: {error}")
            return None

    async def sign_message_and_login(self, private_key, address, proxy, context):
        """Sign message and login to get token - Working version"""
        url = 'https://tapi.kod.af/signin'
        message = 'X1 Testnet Auth'
        
        Logger.info('Signing and logging in...', {"emoji": "🔐", "context": context})
        
        try:
            # Use web3.py to sign message exactly like ethers.js
            from web3 import Web3
            from eth_account.messages import encode_defunct
            import eth_account
            
            # Create account
            account = eth_account.Account.from_key(private_key)
            
            # Encode message for personal_sign (EIP-191)
            # This is what ethers.js signMessage() uses
            message_hash = encode_defunct(text=message)
            
            # Sign the message
            signed_message = account.sign_message(message_hash)
            
            # Get the signature
            signature = signed_message.signature.hex()
            
            # Verify the signature matches the address (for debugging)
            recovered_address = account.recover_message(message_hash, signature=signed_message.signature)
            Logger.debug(f"Recovered address: {recovered_address}", {"context": context})
            Logger.debug(f"Expected address: {account.address}", {"context": context})
            
            # Prepare payload
            payload = {"signature": signature}
            headers = self.get_session_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    data = await response.json()
                    
                    if response.status == 200 and data.get('token'):
                        Logger.info(f"Login successful", {"emoji": "✅", "context": context})
                        return data['token']
                    else:
                        # Try alternative: sign with web3.eth.account.sign_message
                        try:
                            w3 = Web3()
                            signed = w3.eth.account.sign_message(
                                {"message": message},
                                private_key
                            )
                            alt_signature = signed.signature.hex()
                            
                            # Try with alternative signature
                            async with session.post(url, json={"signature": alt_signature}, headers=headers, timeout=10) as alt_response:
                                alt_data = await alt_response.json()
                                if alt_response.status == 200 and alt_data.get('token'):
                                    Logger.info(f"Login successful with web3 sign", {"emoji": "✅", "context": context})
                                    return alt_data['token']
                        except:
                            pass
                        
                        error_msg = data.get('error', data.get('message', str(data)))
                        raise ValueError(f"Login failed: {error_msg}")
                            
        except Exception as error:
            Logger.error(f"Failed to sign and login: {error}", {"emoji": "❌", "context": context})
            return None

    async def get_quests(self, token, context):
        """Get available quests"""
        url = 'https://tapi.kod.af/quests'
        headers = self.get_session_headers(token)
        
        Logger.info('Fetching quests...', {"emoji": "📋", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        raise ValueError(f"Failed to fetch quests: {response.status}")
                        
        except Exception as error:
            Logger.error(f"Failed to fetch quests: {error}", {"emoji": "❌", "context": context})
            return None

    async def complete_quest(self, quest_id, quest_name, token, context):
        """Complete a quest"""
        url = f'https://tapi.kod.af/quests?quest_id={quest_id}'
        headers = self.get_session_headers(token)
        
        Logger.info(f"Completing quest {quest_name}...", {"emoji": "🎯", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, timeout=30) as response:
                    data = await response.json()
                    
                    if response.status == 400 or not data.get('message', '').lower().count('success'):
                        Logger.warn(f"Quest {quest_name} {data.get('message', 'already completed')}", 
                                   {"emoji": "⚠️", "context": context})
                        return {"success": False, "message": data.get('message', 'Already completed')}
                    
                    Logger.info(f"Quest {quest_name} Completed! Reward: {data.get('reward', 'N/A')}", 
                               {"emoji": "✅", "context": context})
                    return {"success": True}
                    
        except Exception as error:
            Logger.error(f"Failed to complete quest {quest_name}: {error}", 
                        {"emoji": "❌", "context": context})
            return None

    async def claim_faucet(self, address, context):
        """Claim faucet"""
        url = f'https://nft-api.x1.one/testnet/faucet?address={address}'
        
        Logger.info('Claiming faucet...', {"emoji": "💧", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.text()
                        if data == 'ok':
                            Logger.info('Faucet claimed successfully!', 
                                       {"emoji": "✅", "context": context})
                            return {"success": True}
                        else:
                            raise ValueError("Faucet claim failed")
                    else:
                        raise ValueError(f"Failed to claim faucet: {response.status}")
                        
        except Exception as error:
            Logger.error(f"Failed to claim faucet: {error}", {"emoji": "❌", "context": context})
            return None

    async def send_daily_tx(self, private_key, address, context):
        """Send daily transaction"""
        rpc_url = 'https://maculatus-rpc.x1eco.com'
        chain_id = 10778
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            account = Account.from_key(private_key)
            
            # Generate random address
            random_account = Account.create()
            random_address = random_account.address
            
            # Random amount between 0.1 and 0.5
            amount = random.uniform(0.1, 0.5)
            
            # Convert to wei
            value = w3.to_wei(amount, 'ether')
            
            Logger.info(f"Sending {amount:.6f} X1T to {mask_address(random_address)}...", 
                       {"emoji": "📤", "context": context})
            
            # Build transaction
            nonce = w3.eth.get_transaction_count(account.address)
            gas_price = w3.eth.gas_price
            
            tx = {
                'nonce': nonce,
                'to': random_address,
                'value': value,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': chain_id
            }
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                Logger.info(f"TX sent successfully! Hash: {tx_hash.hex()}", 
                           {"emoji": "✅", "context": context}")
                return {"success": True}
            else:
                raise ValueError("TX failed")
                
        except Exception as error:
            Logger.error(f"Failed to send TX: {error}", {"emoji": "❌", "context": context})
            return None

    async def get_account_info(self, token, private_key, context):
        """Get account information"""
        url = 'https://tapi.kod.af/me'
        headers = self.get_session_headers(token)
        
        Logger.info('Retrieving account info...', {"emoji": "📊", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Get balance from blockchain
                        rpc_url = 'https://maculatus-rpc.x1eco.com'
                        w3 = Web3(Web3.HTTPProvider(rpc_url))
                        account = Account.from_key(private_key)
                        balance_wei = w3.eth.get_balance(account.address)
                        balance = w3.from_wei(balance_wei, 'ether')
                        
                        return {
                            'address': data.get('address', ''),
                            'points': data.get('points', 0),
                            'rank': data.get('rank', 0),
                            'balance': float(balance)
                        }
                    else:
                        raise ValueError(f"Failed to get account info: {response.status}")
                        
        except Exception as error:
            Logger.error(f"Failed to retrieve account info: {error}", 
                        {"emoji": "❌", "context": context})
            return None

    async def get_public_ip(self, context):
        """Get public IP address"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org?format=json', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('ip', 'Unknown')
                    else:
                        return 'Error retrieving IP'
                        
        except Exception as error:
            Logger.error(f"Failed to get IP: {error}", {"emoji": "❌", "context": context})
            return 'Error retrieving IP'

    async def process_account(self, account, index, total):
        """Process a single account"""
        context = f"Account {index + 1}/{total}"
        
        Logger.info(f"Starting account processing", {"emoji": "🚀", "context": context})
        
        private_key = account['privateKey']
        address = self.derive_wallet_address(private_key)
        
        if not address:
            Logger.error('Invalid private key', {"emoji": "❌", "context": context})
            return
        
        # Print account info
        print_header(f"Account Info {context}")
        print_info('Masked Address', mask_address(address), context)
        
        ip = await self.get_public_ip(context)
        print_info('IP', ip, context)
        print("\n")
        
        try:
            # Authenticate and get token
            token = await self.sign_message_and_login(private_key, address, None, context)
            if not token:
                return
            
            await delay(5)
            print("\n")
            
            # Daily Login Quest
            Logger.info('Starting Daily Checkin Process...', {"emoji": "🛎️", "context": context})
            quests = await self.get_quests(token, context)
            
            if quests:
                daily_login_quest = next((q for q in quests if q.get('title') == 'Daily Login'), None)
                
                if not daily_login_quest:
                    Logger.warn('Daily Login quest not found.', {"emoji": "⚠️", "context": context})
                elif not daily_login_quest.get('is_completed_today', True):
                    checkin_result = await self.complete_quest(
                        daily_login_quest['id'], 'Daily Login', token, context
                    )
                    if checkin_result and checkin_result.get('success'):
                        await delay(5)
                else:
                    Logger.warn('Already Checked-In Today.', {"emoji": "⚠️", "context": context})
            
            await delay(2)
            print("\n")
            
            # Claim Faucet Quest
            Logger.info('Starting Claim Faucet Process...', {"emoji": "💧", "context": context})
            quests = await self.get_quests(token, context)
            
            if quests:
                faucet_quest = next((q for q in quests if q.get('title') == 'Claim Faucet'), None)
                
                if not faucet_quest:
                    Logger.warn('Claim Faucet quest not found.', {"emoji": "⚠️", "context": context})
                elif not faucet_quest.get('is_completed_today', True):
                    faucet_result = await self.claim_faucet(address, context)
                    
                    if faucet_result and faucet_result.get('success'):
                        await delay(5)
                        complete_result = await self.complete_quest(
                            faucet_quest['id'], 'Claim Faucet', token, context
                        )
                        if complete_result and complete_result.get('success'):
                            await delay(5)
                else:
                    Logger.warn('Already Claimed Faucet Today.', {"emoji": "⚠️", "context": context})
            
            await delay(2)
            print("\n")
            
            # Send X1T Quest
            Logger.info('Starting Daily TX Process...', {"emoji": "📤", "context": context})
            quests = await self.get_quests(token, context)
            
            if quests:
                send_x1t_quest = next((q for q in quests if q.get('title') == 'Send X1T'), None)
                
                if not send_x1t_quest:
                    Logger.warn('Send X1T quest not found.', {"emoji": "⚠️", "context": context})
                elif not send_x1t_quest.get('is_completed_today', True):
                    tx_result = await self.send_daily_tx(private_key, address, context)
                    
                    if tx_result and tx_result.get('success'):
                        await delay(5)
                        complete_result = await self.complete_quest(
                            send_x1t_quest['id'], 'Send X1T', token, context
                        )
                        if complete_result and complete_result.get('success'):
                            await delay(5)
                else:
                    Logger.warn('Already Sent TX Today.', {"emoji": "⚠️", "context": context})
            
            await delay(2)
            print("\n")
            await delay(5)
            
            # Get account info
            account_info = await self.get_account_info(token, private_key, context)
            if account_info:
                print_profile_info(
                    account_info['address'],
                    account_info['points'],
                    account_info['rank'],
                    account_info['balance'],
                    context
                )
            
            Logger.info(f"Completed account processing", {"emoji": "🎉", "context": context})
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            
        except Exception as error:
            Logger.error(f"Error processing account: {error}", {"emoji": "❌", "context": context})

    async def initialize_config(self):
        """Initialize configuration"""
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        use_proxy = input(f"{Fore.CYAN}🔌 Do You Want to Use Proxy? (y/n): {Style.RESET_ALL}").strip().lower()
        
        if use_proxy == 'y':
            self.global_use_proxy = True
            self.global_proxies = await self.read_proxies()
            
            if not self.global_proxies:
                self.global_use_proxy = False
                Logger.warn('No proxies available, proceeding without proxy.', {"emoji": "⚠️"})
        else:
            Logger.info('Proceeding without proxy.', {"emoji": "ℹ️"})

    async def run_cycle(self):
        """Run a complete cycle for all accounts"""
        accounts = await self.read_accounts()
        
        if not accounts:
            Logger.error('No accounts found in pk.txt. Exiting cycle.', {"emoji": "❌"})
            return
        
        for i, account in enumerate(accounts):
            try:
                await self.process_account(account, i, len(accounts))
            except Exception as error:
                Logger.error(f"Error processing account: {error}", 
                           {"emoji": "❌", "context": f"Account {i+1}/{len(accounts)}"})
            
            if i < len(accounts) - 1:
                print("\n\n")
                await delay(random.randint(10, 15))

    async def run(self):
        """Main run function"""
        # Display banner
        terminal_width = 80
        
        # Create ASCII art banner
        try:
            ascii_art = text2art("NT EXHAUST", font="block")
            print(f"{Fore.CYAN}{ascii_art}{Style.RESET_ALL}")
        except:
            # Fallback if text2art fails
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'NT EXHAUST'.center(80)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Print channel info
        channel_line = "=== Telegram Channel 🚀 : NT Exhaust (@NTExhaust) ==="
        print(f"{Fore.MAGENTA}{center_text(channel_line, terminal_width)}{Style.RESET_ALL}")
        
        # Print bot info
        bot_line = "✪ BOT X1 EcoCHAIN AUTO DAILY ✪"
        print(f"{Fore.MAGENTA}{center_text(bot_line, terminal_width)}{Style.RESET_ALL}")
        print("\n")
        
        # Initialize configuration
        await self.initialize_config()
        
        # Main loop
        while True:
            await self.run_cycle()
            print()
            Logger.info('Cycle completed. Waiting 24 hours...', {"emoji": "🔄"})
            
            # Wait 24 hours (86400 seconds)
            # For testing, you can reduce this to a shorter time
            await delay(86400)

async def main():
    """Main entry point"""
    bot = X1EcoChainBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        Logger.info("Bot stopped by user", {"emoji": "👋"})
        sys.exit(0)
    except Exception as error:
        Logger.error(f"Fatal error: {error}", {"emoji": "❌"})
        sys.exit(1)

if __name__ == "__main__":
    # Check required packages
    required_packages = [
        'aiohttp', 'web3', 'colorama', 'pyfiglet', 'art', 
        'fake_useragent', 'eth_account'
    ]
    
    print(f"{Fore.YELLOW}Checking required packages...{Style.RESET_ALL}")
    
    import subprocess
    import sys
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"{Fore.RED}Installing {package}...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Run the bot
    asyncio.run(main())
