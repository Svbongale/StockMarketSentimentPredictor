# StockMarketSentimentPredictor

**Gemini AI Stock Sentiment Bot**
An autonomous stock market workflow that identifies upcoming earnings for specific US and Indian companies, syncs reminders to your iPhone Calendar, and sends real-time BUY/FLAG alerts to your phone via Telegram based on AI sentiment analysis of quarterly results.

**Features**
- Watchlist Focused: Tracks only the stocks you care about (NSE & US markets).
- AI-Powered Calendar Sync: Uses Gemini 3.1 to find official earnings dates and analyst projections.
- iPhone Integration: Events appear natively in your iOS Calendar with alerts.
- Deep Sentiment Analysis: Scans live web results on earnings day to determine market mood.
- Instant Notifications: Real-time Telegram alerts for "Buy" opportunities.
- Fully Automated: Runs for free on GitHub Actions—no server required.

**Prerequisites**
- Python 3.10+ installed on your Mac/PC.
- Google Cloud Project with Calendar API enabled.
- Google AI Studio Key for Gemini 3.1 access.
- Telegram Bot (created via @BotFather).

**Step-by-Step Setup**

1. Gemini AI Setup
- Go to Google AI Studio.
- Create a new API Key.
- Save this key; you will need it for the GitHub Secrets later.

2. Google Calendar API (iPhone Sync)
- Go to Google Cloud Console.
- Create a project and Enable Google Calendar API.
- Go to APIs & Services > OAuth consent screen. Set it to "External" and add your email as a Test User.
- Go to Credentials > Create Credentials > OAuth client ID (Select "Desktop App").
- Download the JSON file and rename it to credentials.json. Move it to your project folder.
- Run the local auth script once to link your account: "python3 auth_calendar.py"
- This will generate a token.pickle file. Keep this safe.

3. Telegram Bot Setup
- Message @BotFather on Telegram: /newbot.
- Copy your Bot Token.
- Message your new bot to start a chat.
- Get your Chat ID by visiting: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates

4. GitHub Secrets (Mandatory)
- Since we use GitHub Actions for automation, you must hide your keys.
- In your GitHub Repo, go to Settings > Secrets and variables > Actions and add:
  
  **Secret Name                |	    Value Description**
  
  GEMINI_API_KEY             ->   Your Gemini API Key
  TELEGRAM_TOKEN             ->   Your Telegram Bot Token
  TELEGRAM_CHAT_ID           ->   Your Telegram Chat ID
  GOOGLE_CREDENTIALS_BASE64  ->   The Base64 string of your credentials.json
  GOOGLE_TOKEN_BASE64        ->   The Base64 string of your token.pickle


  How to get Base64 strings (Mac/Linux):
  - base64 -i credentials.json | pbcopy  # Paste into GitHub Secret
  - base64 -i token.pickle | pbcopy      # Paste into GitHub Secret

  
  **Usage**
  
  Local Testing
  To run the weekly calendar sync manually:
  - "python3 trade_bot.py --sync"

  To run the daily sentiment analysis:
  - "python3 trade_bot.py --analyze"

 **Automation Schedule**
 - The bot is pre-configured to run automatically via .github/workflows/stock_bot.yml:
 - Weekly Sync: Every Sunday at 9:00 AM IST. (Bcoz, Indian stock market opens at 9:15AM IST) 
 - Daily Analysis: Mon-Fri at 4:00 PM IST.
  
  **Troubleshooting**
  - 429 Resource Exhausted: You are hitting Gemini's Free Tier rate limits. The code includes a 20-second "cooldown" between stocks.
  - Do not reduce this sleep time.
  - Calendar Event Not on iPhone: Ensure your iPhone is logged into the same Google account and "Calendars" is toggled ON in:
  - Settings > Calendar > Accounts.
  - NSE Tickers: Always use the .NS suffix for Indian stocks (e.g., RELIANCE.NS).

  **License**
  **MIT License. For educational and personal use only. Not financial advice.**

