import os
import schedule
import time
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests
from newsapi import NewsApiClient
import pandas as pd
import logging
from typing import List, Dict, Any
import json
import sys
import traceback

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging with absolute path
log_file = os.path.join(SCRIPT_DIR, 'crypto_report.log')
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Log script start and environment
logging.info(f"Script started from directory: {SCRIPT_DIR}")
logging.info(f"Python executable: {sys.executable}")
logging.info(f"Python version: {sys.version}")

# Load environment variables from the script's directory
logging.info("Loading environment variables from system...")
 
# Verify required environment variables
required_env_vars = ['NEWS_API_KEY', 'EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars: 
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1) 
else:
    logging.info("All required environment variables are present")

# Initialize News API client
try:
    newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
    logging.info("News API client initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize News API client: {e}")
    sys.exit(1)

# Constants
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
CRYPTO_SYMBOLS = ['bitcoin', 'ethereum', 'binancecoin', 'solana']
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def make_api_request(url: str, retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Make an API request with retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                logging.error(f"API request failed after {retries} attempts: {e}")
                raise
            logging.warning(f"API request failed, retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

def get_crypto_news() -> List[Dict[str, Any]]:
    """Fetch latest cryptocurrency news"""
    try:
        news = newsapi.get_everything(
            q='cryptocurrency OR bitcoin OR ethereum',
            language='en',
            sort_by='publishedAt',
            page_size=10
        )
        return news['articles']
    except Exception as e:
        logging.error(f"Error fetching crypto news: {e}")
        return []

def get_political_news() -> List[Dict[str, Any]]:
    """Fetch political news that might affect crypto"""
    try:
        news = newsapi.get_everything(
            q='(regulation OR policy OR government) AND (cryptocurrency OR bitcoin OR crypto)',
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        return news['articles']
    except Exception as e:
        logging.error(f"Error fetching political news: {e}")
        return []

def get_crypto_market_summary() -> List[Dict[str, Any]]:
    """Get 24-hour crypto market summary using CoinGecko API"""
    try:
        summary = []
        crypto_ids = ','.join(CRYPTO_SYMBOLS)
        url = f"{COINGECKO_API_URL}/simple/price?ids={crypto_ids}&vs_currencies=usd&include_24hr_change=true"
        
        data = make_api_request(url)
        
        for crypto in CRYPTO_SYMBOLS:
            if crypto in data:
                price = data[crypto]['usd']
                change = data[crypto]['usd_24h_change']
                
                summary.append({
                    'symbol': crypto.upper(),
                    'price': price,
                    'change_24h': change
                })
            else:
                logging.warning(f"No data available for {crypto}")
        
        if not summary:
            summary.append({
                'symbol': 'N/A',
                'price': 0,
                'change_24h': 0,
                'message': 'Crypto price data temporarily unavailable'
            })
        
        return summary
    except Exception as e:
        logging.error(f"Error in market summary: {e}")
        return [{
            'symbol': 'N/A',
            'price': 0,
            'change_24h': 0,
            'message': 'Market data temporarily unavailable'
        }]

def format_email_content(crypto_news, political_news, market_summary):
    """Format the email content"""
    html_content = f"""
    <html>
        <body>
            <h2>Crypto Daily Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
    """
    
    # Add market summary section
    html_content += """
            <h3>Market Summary (24h)</h3>
            <table border="1">
                <tr>
                    <th>Cryptocurrency</th>
                    <th>Price (USD)</th>
                    <th>24h Change (%)</th>
                </tr>
    """
    
    for crypto in market_summary:
        if 'message' in crypto:
            html_content += f"""
                <tr>
                    <td colspan="3" style="text-align: center; color: red;">{crypto['message']}</td>
                </tr>
            """
        else:
            html_content += f"""
                <tr>
                    <td>{crypto['symbol']}</td>
                    <td>${crypto['price']:,.2f}</td>
                    <td>{crypto['change_24h']:,.2f}%</td>
                </tr>
            """
    
    html_content += """
            </table>
    """
    
    # Add crypto news section
    if crypto_news:
        html_content += """
            <h3>Latest Crypto News</h3>
            <ul>
        """
        
        for article in crypto_news:
            html_content += f"""
                <li>
                    <a href="{article['url']}">{article['title']}</a>
                    <br>
                    <small>{article['description']}</small>
                </li>
            """
        
        html_content += """
            </ul>
        """
    else:
        html_content += """
            <h3>Latest Crypto News</h3>
            <p>No crypto news available at the moment.</p>
        """
    
    # Add political news section
    if political_news:
        html_content += """
            <h3>Political News Affecting Crypto</h3>
            <ul>
        """
        
        for article in political_news:
            html_content += f"""
                <li>
                    <a href="{article['url']}">{article['title']}</a>
                    <br>
                    <small>{article['description']}</small>
                </li>
            """
        
        html_content += """
            </ul>
        """
    else:
        html_content += """
            <h3>Political News Affecting Crypto</h3>
            <p>No political news available at the moment.</p>
        """
    
    html_content += """
        </body>
    </html>
    """
    
    return html_content

def send_email(content: str) -> None:
    """Send the email report"""
    try:
        logging.info("Preparing to send email...")
        required_env_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Crypto Daily Report - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = os.getenv('EMAIL_SENDER')
        msg['To'] = os.getenv('EMAIL_RECIPIENT')
        
        logging.info(f"Email prepared for: {os.getenv('EMAIL_RECIPIENT')}")
        
        msg.attach(MIMEText(content, 'html'))
        
        logging.info("Attempting to connect to SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            logging.info("Connected to SMTP server, attempting login...")
            smtp_server.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
            logging.info("Login successful, sending email...")
            smtp_server.sendmail(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_RECIPIENT'), msg.as_string())
        
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
        raise

def generate_and_send_report() -> None:
    """Generate and send the daily report"""
    logging.info("Generating daily report...")
    
    try:
        # Fetch all required data
        logging.info("Fetching crypto news...")
        crypto_news = get_crypto_news()
        logging.info(f"Retrieved {len(crypto_news)} crypto news articles")
        
        logging.info("Fetching political news...")
        political_news = get_political_news()
        logging.info(f"Retrieved {len(political_news)} political news articles")
        
        logging.info("Fetching market summary...")
        market_summary = get_crypto_market_summary()
        logging.info("Market summary retrieved")
        
        # Format and send email
        logging.info("Formatting email content...")
        email_content = format_email_content(crypto_news, political_news, market_summary)
        logging.info("Email content formatted, attempting to send...")
        send_email(email_content)
        
        logging.info("Daily report generated and sent successfully")
    except Exception as e:
        logging.error(f"Failed to generate and send report: {e}")
        logging.error(f"Full traceback: {traceback.format_exc()}")

def main() -> None:
    """Main function to schedule and run the report"""
    logging.info("Starting Crypto News Automation...")
    
    try:
        # Schedule the report for 10 AM daily
        schedule.every().day.at("10:00").do(generate_and_send_report)
        logging.info("Report scheduled for 10:00 AM daily")
        
        # Run the report immediately on startup
        logging.info("Running initial report...")
        generate_and_send_report()
        
        # Keep the script running with improved scheduling
        logging.info("Entering main scheduling loop...")
        while True:
            try:
                schedule.run_pending()
                # Calculate sleep time until next minute
                now = datetime.now()
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                sleep_time = (next_minute - now).total_seconds()
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                logging.error(f"Full traceback: {traceback.format_exc()}")
                time.sleep(60)  # Fallback sleep time
    except Exception as e:
        logging.error(f"Fatal error in main: {e}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 