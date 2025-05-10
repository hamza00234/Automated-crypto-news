# Crypto News and Report Automation

This application automatically collects and sends cryptocurrency news, political news affecting crypto, and daily crypto reports via email.

## Features
- Daily crypto news collection
- Political news monitoring affecting crypto markets
- 24-hour crypto market summary
- Automated email delivery
- Scheduled daily reports at 10 AM

## Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```
NEWS_API_KEY=your_newsapi_key
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
EMAIL_RECIPIENT=recipient_email@example.com
```

3. Run the application:
```bash
python main.py
```

## Note
- You'll need a News API key from https://newsapi.org/
- For Gmail, you'll need to use an App Password instead of your regular password
- The application will run continuously and send reports daily at 10 AM 