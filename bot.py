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
    return asyncio.sleep(seconds)

async def countdown(seconds, message):
    for remaining in range(seconds, 0, -1):
        print(f"\r{message} {remaining}s remaining...", end="", flush=True)
        await asyncio.sleep(1)
    print("\r" + " " * 50 + "\r", end="", flush=True)

def center_text(text, width):
    clean_text = re.sub(r'\x1B\[[0-9;]*[mK]', '', text)
    text_length = len(clean_text)
    total_padding = max(0, width - text_length)
    left_padding = total_padding // 2
    right_padding = total_padding - left_padding
    return " " * left_padding + text + " " * right_padding

def print_header(title):
    width = 80
    print(f"{Fore.CYAN}┬{'─' * (width - 2)}┬{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│ {title.ljust(width - 4)} │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}┴{'─' * (width - 2)}┴{Style.RESET_ALL}")

def print_info(label, value, context):
    Logger.info(f"{label.ljust(15)}: {Fore.CYAN}{value}{Style.RESET_ALL}", 
                {"emoji": "📍 ", "context": context})

def print_profile_info(address, points, rank, balance, context):
    print_header(f"Profile Info {context}")
    print_info('Wallet Address', mask_address(address), context)
    print_info('Total Points', str(points), context)
    print_info('Rank', str(rank), context)
    print_info('X1T Balance', str(balance), context)
    print("\n")

def mask_address(address):
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
        return self.user_agent.random

    def get_session_headers(self, token=None):
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

    async def read_accounts(self):
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
        try:
            account = Account.from_key(private_key)
            return account.address
        except Exception as error:
            Logger.error(f"Failed to derive address: {error}")
            return None

    async def sign_message_and_login(self, private_key, address, proxy, context):
        """Sign message exactly like ethers.js wallet.signMessage()"""
        url = 'https://tapi.kod.af/signin'
        message = 'X1 Testnet Auth'  # Must be plain string
        
        Logger.info('Signing and logging in...', {"emoji": "🔐", "context": context})
        
        try:
            # This is the exact equivalent of ethers.js signMessage
            message_hash = encode_defunct(text=message)
            account = Account.from_key(private_key)
            signed = account.sign_message(message_hash)
            signature = signed.signature.hex()
            
            # Local verification
            recovered = Account.recover_message(message_hash, signature=signed.signature)
            Logger.debug(f"Recovered: {recovered.lower()}", {"context": context})
            Logger.debug(f"Expected : {address.lower()}", {"context": context})
            
            if recovered.lower() != address.lower():
                raise ValueError("Signature verification failed locally!")
            
            payload = {"signature": signature}
            headers = self.get_session_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
                    data = await resp.json()
                    
                    if resp.status == 200 and data.get('token'):
                        Logger.info("Login successful!", {"emoji": "✅", "context": context})
                        return data['token']
                    else:
                        err = data.get('error') or data.get('message') or str(data)
                        raise ValueError(f"Login failed: {err}")
                        
        except Exception as e:
            Logger.error(f"Failed to sign and login: {e}", {"emoji": "❌", "context": context})
            return None

    async def get_quests(self, token, context):
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
        url = f'https://tapi.kod.af/quests?quest_id={quest_id}'
        headers = self.get_session_headers(token)
        
        Logger.info(f"Completing quest {quest_name}...", {"emoji": "🎯", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, timeout=30) as response:
                    data = await response.json()
                    
                    if response.status == 400 or 'success' not in data.get('message', '').lower():
                        Logger.warn(f"Quest {quest_name}: {data.get('message', 'already completed')}", 
                                   {"emoji": "⚠️", "context": context})
                        return {"success": False}
                    
                    Logger.info(f"Quest {quest_name} Completed! Reward: {data.get('reward', 'N/A')}", 
                               {"emoji": "✅", "context": context})
                    return {"success": True}
                    
        except Exception as error:
            Logger.error(f"Failed to complete quest {quest_name}: {error}", 
                        {"emoji": "❌", "context": context})
            return None

    async def claim_faucet(self, address, context):
        url = f'https://nft-api.x1.one/testnet/faucet?address={address}'
        
        Logger.info('Claiming faucet...', {"emoji": "💧", "context": context})
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200 and (await response.text()) == 'ok':
                        Logger.info('Faucet claimed successfully!', {"emoji": "✅", "context": context})
                        return {"success": True}
                    else:
                        raise ValueError("Faucet claim failed")
                        
        except Exception as error:
            Logger.error(f"Failed to claim faucet: {error}", {"emoji": "❌", "context": context})
            return None

    async def send_daily_tx(self, private_key, address, context):
        rpc_url = 'https://maculatus-rpc.x1eco.com'
        chain_id = 10778
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            account = Account.from_key(private_key)
            random_addr = Account.create().address
            amount = random.uniform(0.1, 0.5)
            value = w3.to_wei(amount, 'ether')
            
            Logger.info(f"Sending {amount:.6f} X1T to {mask_address(random_addr)}...", 
                       {"emoji": "📤", "context": context})
            
            nonce = w3.eth.get_transaction_count(account.address)
            gas_price = w3.eth.gas_price
            
            tx = {
                'nonce': nonce,
                'to': random_addr,
                'value': value,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': chain_id
            }
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                Logger.info(f"TX sent successfully! Hash: {tx_hash.hex()}", 
                           {"emoji": "✅", "context": context})
                return {"success": True}
            else:
                raise ValueError("TX failed")
                
        except Exception as error:
            Logger.error(f"Failed to send TX: {error}", {"emoji": "❌", "context": context})
            return None

    async def get_account_info(self, token, private_key, context):
        url = 'https://tapi.kod.af/me'
        headers = self.get_session_headers(token)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        w3 = Web3(Web3.HTTPProvider('https://maculatus-rpc.x1eco.com'))
                        balance = w3.from_wei(w3.eth.get_balance(data.get('address', '')), 'ether')
                        return {
                            'address': data.get('address', ''),
                            'points': data.get('points', 0),
                            'rank': data.get('rank', 0),
                            'balance': float(balance)
                        }
        except Exception as error:
            Logger.error(f"Failed to get info: {error}", {"emoji": "❌", "context": context})
            return None

    async def get_public_ip(self, context):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.ipify.org?format=json', timeout=10) as resp:
                    if resp.status == 200:
                        return (await resp.json()).get('ip', 'Unknown')
        except:
            return 'Error'

    async def process_account(self, account, index, total):
        context = f"Account {index + 1}/{total}"
        Logger.info("Starting processing", {"emoji": "🚀", "context": context})
        
        private_key = account['privateKey']
        address = self.derive_wallet_address(private_key)
        if not address: return
        
        print_header(f"Account Info {context}")
        print_info('Masked Address', mask_address(address), context)
        print_info('IP', await self.get_public_ip(context), context)
        print("\n")
        
        token = await self.sign_message_and_login(private_key, address, None, context)
        if not token: return
        
        await delay(5)
        print("\n")
        
        # Daily Login
        Logger.info('Daily Checkin...', {"emoji": "🛎️", "context": context})
        quests = await self.get_quests(token, context)
        if quests:
            daily = next((q for q in quests if q.get('title') == 'Daily Login'), None)
            if daily and not daily.get('is_completed_today', True):
                await self.complete_quest(daily['id'], 'Daily Login', token, context)
                await delay(5)
        
        await delay(3)
        print("\n")
        
        # Faucet
        Logger.info('Claim Faucet...', {"emoji": "💧", "context": context})
        quests = await self.get_quests(token, context)
        if quests:
            faucet = next((q for q in quests if q.get('title') == 'Claim Faucet'), None)
            if faucet and not faucet.get('is_completed_today', True):
                if await self.claim_faucet(address, context):
                    await delay(5)
                    await self.complete_quest(faucet['id'], 'Claim Faucet', token, context)
        
        await delay(3)
        print("\n")
        
        # Send TX
        Logger.info('Daily TX...', {"emoji": "📤", "context": context})
        quests = await self.get_quests(token, context)
        if quests:
            send = next((q for q in quests if q.get('title') == 'Send X1T'), None)
            if send and not send.get('is_completed_today', True):
                if await self.send_daily_tx(private_key, address, context):
                    await delay(5)
                    await self.complete_quest(send['id'], 'Send X1T', token, context)
        
        await delay(5)
        info = await self.get_account_info(token, private_key, context)
        if info:
            print_profile_info(info['address'], info['points'], info['rank'], info['balance'], context)
        
        Logger.info("Account completed", {"emoji": "🎉", "context": context})
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

    async def initialize_config(self):
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        ans = input(f"{Fore.CYAN}🔌 Use Proxy? (y/n): {Style.RESET_ALL}").strip().lower()
        if ans == 'y':
            self.global_use_proxy = True
            self.global_proxies = await self.read_proxies()
            if not self.global_proxies:
                self.global_use_proxy = False
                Logger.warn('No proxies, running without proxy.', {"emoji": "⚠️"})
        else:
            Logger.info('Running without proxy.', {"emoji": "ℹ️"})

    async def run_cycle(self):
        accounts = await self.read_accounts()
        if not accounts: return
        
        for i, acc in enumerate(accounts):
            await self.process_account(acc, i, len(accounts))
            if i < len(accounts)-1:
                await delay(random.randint(10, 20))

    async def run(self):
        try:
            ascii_art = text2art("NT EXHAUST", font="block")
            print(f"{Fore.CYAN}{ascii_art}{Style.RESET_ALL}")
        except:
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'NT EXHAUST'.center(80)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        print(f"{Fore.MAGENTA}{center_text('=== Telegram Channel 🚀 : NT Exhaust (@NTExhaust) ===', 80)}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{center_text('✪ BOT X1 EcoCHAIN AUTO DAILY ✪', 80)}{Style.RESET_ALL}")
        print("\n")
        
        await self.initialize_config()
        
        while True:
            await self.run_cycle()
            Logger.info('Cycle done. Waiting 24h...', {"emoji": "🔄"})
            await delay(86400)

async def main():
    bot = X1EcoChainBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        Logger.info("Stopped by user", {"emoji": "👋"})
    except Exception as e:
        Logger.error(f"Fatal: {e}", {"emoji": "❌"})

if __name__ == "__main__":
    required = ['aiohttp','web3','colorama','pyfiglet','art','fake_useragent','eth_account']
    print(f"{Fore.YELLOW}Checking packages...{Style.RESET_ALL}")
    for pkg in required:
        try:
            __import__(pkg.replace('-','_'))
        except ImportError:
            print(f"{Fore.RED}Installing {pkg}...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
    asyncio.run(main())
