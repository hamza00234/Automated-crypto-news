import os
import schedule
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests
from newsapi import NewsApiClient
import logging
from typing import List, Dict, Any
import sys
import traceback

# Load .env only if not running on Railway
if not os.getenv("RAILWAY_ENV"):
    load_dotenv()

# Setup logging to file and console
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(SCRIPT_DIR, 'crypto_report.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Check required env vars
required_env_vars = [
    'NEWS_API_KEY',
    'EMAIL_SENDER',
    'EMAIL_PASSWORD',
    'EMAIL_RECIPIENT',
    'EMAIL_RECIPIENT2'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Initialize News API client
try:
    newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
except Exception as e:
    logging.error(f"Failed to initialize News API client: {e}")
    sys.exit(1)

# Constants
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
CRYPTO_SYMBOLS = ['bitcoin', 'ethereum', 'celestia', 'solana']
MAX_RETRIES = 3
RETRY_DELAY = 5


def make_api_request(url: str, retries: int = MAX_RETRIES) -> Dict[str, Any]:
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                logging.error(f"API request failed: {e}")
                raise
            logging.warning(f"API request failed, retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)


def get_crypto_news() -> List[Dict[str, Any]]:
    try:
        news = newsapi.get_everything(
            q='cryptocurrency OR bitcoin OR ethereum',
            language='en',
            sort_by='publishedAt',
            page_size=10
        )
        return news.get('articles', [])
    except Exception as e:
        logging.error(f"Error fetching crypto news: {e}")
        return []


def get_political_news() -> List[Dict[str, Any]]:
    try:
        news = newsapi.get_everything(
            q='(regulation OR policy OR government) AND (cryptocurrency OR bitcoin OR crypto)',
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
        return news.get('articles', [])
    except Exception as e:
        logging.error(f"Error fetching political news: {e}")
        return []


def get_crypto_market_summary() -> List[Dict[str, Any]]:
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
                logging.warning(f"No data for {crypto}")

        if not summary:
            summary.append({
                'symbol': 'N/A',
                'price': 0,
                'change_24h': 0,
                'message': 'Crypto data unavailable'
            })

        return summary
    except Exception as e:
        logging.error(f"Market summary error: {e}")
        return [{
            'symbol': 'N/A',
            'price': 0,
            'change_24h': 0,
            'message': 'Market data error'
        }]


def format_email_content(crypto_news, political_news, market_summary):
    html = f"""
    <html><body>
        <h2>Crypto Daily Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
        <h3>Market Summary</h3>
        <table border="1" cellpadding="5">
            <tr><th>Crypto</th><th>Price (USD)</th><th>24h Change (%)</th></tr>
    """
    for crypto in market_summary:
        if 'message' in crypto:
            html += f"<tr><td colspan='3'>{crypto['message']}</td></tr>"
        else:
            html += f"<tr><td>{crypto['symbol']}</td><td>${crypto['price']:,.2f}</td><td>{crypto['change_24h']:,.2f}%</td></tr>"
    html += "</table>"

    html += "<h3>Crypto News</h3><ul>"
    if crypto_news:
        for article in crypto_news:
            title = article.get('title', 'No title')
            url = article.get('url', '#')
            description = article.get('description', '')
            html += f"<li><a href='{url}'>{title}</a><br><small>{description}</small></li>"
    else:
        html += "<p>No crypto news available.</p>"
    html += "</ul>"

    html += "<h3>Political News</h3><ul>"
    if political_news:
        for article in political_news:
            title = article.get('title', 'No title')
            url = article.get('url', '#')
            description = article.get('description', '')
            html += f"<li><a href='{url}'>{title}</a><br><small>{description}</small></li>"
    else:
        html += "<p>No political news available.</p>"
    html += "</ul></body></html>"

    return html


def send_email(content: str):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Crypto Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = os.getenv('EMAIL_SENDER')
        recipients = [os.getenv('EMAIL_RECIPIENT'), os.getenv('EMAIL_RECIPIENT2')]
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
            server.sendmail(os.getenv('EMAIL_SENDER'), recipients, msg.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        logging.error(traceback.format_exc())


def generate_and_send_report():
    logging.info("Generating and sending report...")
    try:
        crypto_news = get_crypto_news()
        political_news = get_political_news()
        market_summary = get_crypto_market_summary()

        email_content = format_email_content(crypto_news, political_news, market_summary)
        send_email(email_content)
    except Exception as e:
        logging.error(f"Error in report generation: {e}")
        logging.error(traceback.format_exc())


def run_scheduler():
    schedule.every(3).hours.do(generate_and_send_report)
    generate_and_send_report()  # Run immediately on startup
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
