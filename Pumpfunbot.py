import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Set, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PumpFunMonitor:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        self.seen_tokens: Set[str] = set()
        self.session = None
        
        # Pump.fun API endpoints (these may need adjustment based on actual API)
        self.pumpfun_api = "https://frontend-api.pump.fun"
        self.tokens_endpoint = f"{self.pumpfun_api}/coins"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_telegram_message(self, message: str, parse_mode: str = "HTML"):
        """Send message to Telegram"""
        url = f"{self.telegram_api}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info("Message sent successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send message: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")

    async def get_new_tokens(self) -> list:
        """Fetch new tokens from pump.fun API"""
        try:
            # This endpoint structure may need adjustment based on actual pump.fun API
            params = {
                "limit": 50,
                "offset": 0,
                "sort": "created_timestamp",
                "order": "DESC"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            
            async with self.session.get(self.tokens_endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data if isinstance(data, list) else data.get('coins', [])
                else:
                    logger.error(f"API request failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return []

    def format_token_message(self, token: Dict[str, Any]) -> str:
        """Format token information for Telegram message"""
        try:
            # Extract token information (adjust field names based on actual API response)
            name = token.get('name', 'Unknown')
            symbol = token.get('symbol', 'N/A')
            mint = token.get('mint', 'N/A')
            description = token.get('description', 'No description available')
            
            # Market data
            market_cap = token.get('usd_market_cap', 0)
            price = token.get('price_usd', 0)
            creator = token.get('creator', 'Unknown')
            
            # Social links
            website = token.get('website', '')
            telegram = token.get('telegram', '')
            twitter = token.get('twitter', '')
            
            # Format market cap and price
            market_cap_formatted = f"${market_cap:,.2f}" if market_cap else "N/A"
            price_formatted = f"${float(price):.8f}" if price else "N/A"
            
            # Create message
            message = f"""
🚀 <b>NEW TOKEN LISTED ON PUMP.FUN</b>

💎 <b>Name:</b> {name}
🎯 <b>Symbol:</b> ${symbol}
🔑 <b>Contract:</b> <code>{mint}</code>
👤 <b>Creator:</b> <code>{creator}</code>

💰 <b>Price:</b> {price_formatted}
📊 <b>Market Cap:</b> {market_cap_formatted}

📝 <b>Description:</b>
{description[:200]}{'...' if len(description) > 200 else ''}

🔗 <b>Links:</b>
• Pump.fun: https://pump.fun/{mint}
• DEXScreener: https://dexscreener.com/solana/{mint}
• Birdeye: https://birdeye.so/token/{mint}
"""
            
            # Add social links if available
            if website:
                message += f"• Website: {website}\n"
            if twitter:
                message += f"• Twitter: {twitter}\n"
            if telegram:
                message += f"• Telegram: {telegram}\n"
            
            message += f"\n⏰ <b>Detected at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting token message: {e}")
            return f"Error formatting token data: {str(e)}"

    async def monitor_new_tokens(self):
        """Main monitoring loop"""
        logger.info("Starting pump.fun token monitoring...")
        
        # Send startup message
        await self.send_telegram_message("🤖 Pump.fun Token Monitor Started!\nWatching for new token listings...")
        
        while True:
            try:
                tokens = await self.get_new_tokens()
                
                if tokens:
                    for token in tokens:
                        token_mint = token.get('mint', '')
                        if token_mint and token_mint not in self.seen_tokens:
                            # New token found
                            self.seen_tokens.add(token_mint)
                            message = self.format_token_message(token)
                            await self.send_telegram_message(message)
                            
                            # Add small delay between messages to avoid rate limits
                            await asyncio.sleep(2)
                    
                    logger.info(f"Processed {len(tokens)} tokens, {len(self.seen_tokens)} total tracked")
                else:
                    logger.warning("No tokens retrieved from API")
                
                # Wait before next check (adjust interval as needed)
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

async def main():
    # Configuration
    BOT_TOKEN = "8200498127:AAG6W6I6hptzxd4i-N7puelnOPCZr9NT0Cs"
    CHAT_ID = "1129109001"
    
    async with PumpFunMonitor(BOT_TOKEN, CHAT_ID) as monitor:
        await monitor.monitor_new_tokens()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

# Alternative implementation using requests (synchronous)
"""
import requests
import time
from datetime import datetime

class PumpFunMonitorSync:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        self.seen_tokens = set()
        self.session = requests.Session()
        
    def send_message(self, text: str):
        url = f"{self.telegram_api}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            response = self.session.post(url, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def get_tokens(self):
        try:
            response = self.session.get("https://frontend-api.pump.fun/coins")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching tokens: {e}")
            return []
    
    def run(self):
        self.send_message("🤖 Pump.fun Monitor Started!")
        
        while True:
            try:
                tokens = self.get_tokens()
                for token in tokens:
                    mint = token.get('mint', '')
                    if mint and mint not in self.seen_tokens:
                        self.seen_tokens.add(mint)
                        # Format and send message here
                        message = f"New token: {token.get('name', 'Unknown')}"
                        self.send_message(message)
                        
                time.sleep(30)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

# To run sync version:
# monitor = PumpFunMonitorSync("YOUR_BOT_TOKEN", "YOUR_CHAT_ID")
# monitor.run()
"""
