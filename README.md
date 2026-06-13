# Telegram AliExpress Affiliate Relay

Turn any Telegram channel with product links into a monetized feed in minutes.  
This script **listens to a source channel**, **detects the first URL in each new message**, **converts it to an AliExpress affiliate link**, and **reposts the updated message** to a target channel automatically.

<p align="left">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-blue.svg"></a>
  <a href="https://docs.telethon.dev/"><img alt="Telethon" src="https://img.shields.io/badge/Telethon-async-green.svg"></a>
  <img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen.svg">
</p>

---

## Why this is useful
- **Hands‑off monetization:** keep posting as usual—links get converted automatically.
- **Fast time‑to‑value:** simple .env config, one command to run.
- **Trackable results:** uses your AliExpress `tracking_id` (PID) for attribution.

---

## What it does
- Watches a **source channel** (`SOURCE_CHANNEL_ID`) for new messages.
- Parses the **first URL** in the message body (regex `https?://\S+`).
- Converts that URL into an **AliExpress affiliate link** using `AliexpressApi` (`KEY`, `SECRET`, `TRACKING_ID` required).
- **Replaces** the original URL with the affiliate one and **forwards** the message to the **target channel** (`TARGET_CHANNEL_ID`).
- Logs all important steps and errors; fully **async** on top of **Telethon**.

> If there is no URL or if affiliate conversion fails, the script logs it and skips replacement.

---

## How it works (under the hood)
1. `Telethon` starts a **user session** via `PHONE_NUMBER` (creates `anon.session` on first run).
2. `@client.on(events.NewMessage(chats=SOURCE_CHANNEL_ID))` fires on each new message.
3. `find_link_in_message()` extracts the **first** URL.
4. `generate_affiliate_link()` calls `aliexpress.get_affiliate_links(original_link)` and picks `promotion_link`.
5. The message text is updated and sent to `TARGET_CHANNEL_ID`.

Flow diagram:
```
[Source Channel] --(Telethon)--> [Extract first URL] --(AliExpress API)--> [Replace URL]
         \__________________________________________________________________________/ 
                                      |
                                   Forward
                                      v
                       [Target Channel: affiliate link inside]
```

---

## Installation

> Requires Python **3.9+**.

```bash
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -U telethon python-dotenv aliexpress-api
# Note: some forks of the AliExpress SDK use different names.
# If you see ImportError for `aliexpress_api`, try:
# pip install aliexpress-affiliate-api
```

---

## Configuration (.env)

Create a `.env` file in the project root:

```ini
# AliExpress Affiliate
KEY=your_aliexpress_app_key
SECRET=your_aliexpress_app_secret
TRACKING_ID=your_tracking_id   # PID / trackingId

# Telegram (user session)
API_ID=1234567
API_HASH=your_api_hash
PHONE_NUMBER=+380XXXXXXXXX

# Channel IDs (integer IDs; for supergroups/channels use -100XXXXXXXXXX)
SOURCE_CHANNEL_ID=-1001111111111
TARGET_CHANNEL_ID=-1002222222222
```

**Notes**
- Get `API_ID`/`API_HASH` at https://my.telegram.org.
- Use **numeric IDs** for private channels. You can fetch them via info bots or a small Telethon helper.

---

## Run

```bash
python main.py
```
On the first launch, Telethon will ask for a one‑time code in Telegram to create the local session (`anon.session`). After that, the script runs continuously and relays messages as they arrive.

---

## Features & limitations

- Replaces **only the first** URL per message (extendable to many).
- Designed for **AliExpress** links; non‑AliExpress URLs may be ignored by the SDK.
- Uses a **user session** (not a bot). Ensure the account can **read** from the source and **post** to the target channel.
- Verbose logging explains why a URL wasn’t replaced or a message wasn’t sent.

---

## Troubleshooting

- **ModuleNotFoundError: `aliexpress_api`** → install `aliexpress-api` or try `aliexpress-affiliate-api` depending on the fork you use.
- **Auth loop** on first run → make sure the phone number is valid and you enter the Telegram login code promptly.
- **Wrong channel IDs** → verify you are using **numeric** IDs (often start with `-100` for channels/supergroups).
- **No messages forwarded** → confirm the account has permissions in both channels and that messages actually contain URLs.

--- 

I can build for you **custom Telegram bots, scripts, and automation solutions** — fast, reliable, and scalable.  

**What I can do:**  
- Website automation (simulate user actions, form filling, scheduling)  
- Data collection & web scraping (APIs or no-API scraping)  
- Custom parsers for structured/unstructured data  
- Chatbot development (Telegram, Discord, Slack, WhatsApp)  
- Backend systems & API integrations  

**Goal:** automate routine tasks, collect valuable data, and make your processes more efficient.   

### Contact / Order

<div align="center">

[![Upwork – Hire Me](https://img.shields.io/badge/Upwork-Hire%20Me-6FDA44?logo=upwork&logoColor=white)](https://www.upwork.com/freelancers/~01a13da64f55e1d242?mp_source=share)
[![Fiverr – Order Gig](https://img.shields.io/badge/Fiverr-Order%20Gig-1DBF73?logo=fiverr&logoColor=white)](https://www.fiverr.com/s/99g7N0a)
[![Telegram – Chat](https://img.shields.io/badge/Telegram-Chat-26A5E4?logo=telegram&logoColor=white)](https://t.me/san4o_prog)
[![Email – Contact](https://img.shields.io/badge/Email-Contact-EA4335?logo=gmail&logoColor=white)](mailto:lapchuk.freelancer@gmail.com)

</div>



