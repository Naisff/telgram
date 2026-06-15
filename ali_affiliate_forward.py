import re
import logging
from telethon import TelegramClient, events
from aliexpress_api import AliexpressApi, models
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

URL_PATTERN = re.compile(r'https?://\S+')
API_RETRY_ATTEMPTS = int(os.getenv('API_RETRY_ATTEMPTS', '3'))
API_RETRY_DELAY_SECONDS = float(os.getenv('API_RETRY_DELAY_SECONDS', '2'))
TELEGRAM_RETRY_ATTEMPTS = int(os.getenv('TELEGRAM_RETRY_ATTEMPTS', '3'))
TELEGRAM_RETRY_DELAY_SECONDS = float(os.getenv('TELEGRAM_RETRY_DELAY_SECONDS', '3'))
RECONNECT_DELAY_SECONDS = float(os.getenv('RECONNECT_DELAY_SECONDS', '5'))


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def parse_source_channel_ids():
    raw_ids = os.getenv('SOURCE_CHANNEL_IDS') or os.getenv('SOURCE_CHANNEL_ID')
    if not raw_ids:
        raise ValueError("Missing SOURCE_CHANNEL_IDS or SOURCE_CHANNEL_ID")

    parsed_ids = []
    for item in re.split(r'[\s,;]+', raw_ids.strip()):
        if not item:
            continue
        try:
            parsed_ids.append(int(item))
        except ValueError as exc:
            raise ValueError(f"Invalid channel id '{item}' in SOURCE_CHANNEL_IDS") from exc

    unique_ids = list(dict.fromkeys(parsed_ids))
    if not unique_ids:
        raise ValueError("No valid source channel ids found")
    return unique_ids


# Configuration
KEY = get_required_env('KEY')
SECRET = get_required_env('SECRET')
TRACKING_ID = get_required_env('TRACKING_ID')
API_ID = int(get_required_env('API_ID'))
API_HASH = get_required_env('API_HASH')
PHONE_NUMBER = get_required_env('PHONE_NUMBER')
SOURCE_CHANNEL_IDS = parse_source_channel_ids()
TARGET_CHANNEL_ID = int(get_required_env('TARGET_CHANNEL_ID'))

# Initialize Aliexpress API client
aliexpress = AliexpressApi(KEY, SECRET, models.Language.EN, models.Currency.EUR, TRACKING_ID)

# Initialize Telegram client
client = TelegramClient('anon', API_ID, API_HASH)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_client():
    for attempt in range(1, TELEGRAM_RETRY_ATTEMPTS + 1):
        try:
            if client.is_connected():
                return

            await client.start(PHONE_NUMBER)
            logger.info(
                "Client started. Listening to %s source channels.",
                len(SOURCE_CHANNEL_IDS),
            )
            return
        except Exception as e:
            logger.warning(
                "Telegram start attempt %s/%s failed: %s",
                attempt,
                TELEGRAM_RETRY_ATTEMPTS,
                e,
            )
            if attempt == TELEGRAM_RETRY_ATTEMPTS:
                raise
            await asyncio.sleep(TELEGRAM_RETRY_DELAY_SECONDS * attempt)


@client.on(events.NewMessage(chats=SOURCE_CHANNEL_IDS))
async def message_handler(event):
    try:
        message_text = event.message.message or ""
        original_link = find_link_in_message(message_text)

        if original_link:
            affiliate_link = await generate_affiliate_link(original_link)
            if affiliate_link:
                updated_text = message_text.replace(original_link, affiliate_link, 1)
                await forward_message(event, updated_text)
                logger.info(
                    "Message forwarded from %s with updated affiliate link.",
                    event.chat_id,
                )
            else:
                logger.warning("Failed to create affiliate link")
        else:
            logger.info("No link found in the message")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def find_link_in_message(message):
    match = URL_PATTERN.search(message)
    if match:
        original_link = match.group(0)
        logger.info(f"Found link: {original_link}")
        return original_link
    return None


async def generate_affiliate_link(original_link):
    for attempt in range(1, API_RETRY_ATTEMPTS + 1):
        try:
            affiliate_links = await asyncio.to_thread(
                aliexpress.get_affiliate_links,
                original_link,
            )
            if affiliate_links:
                affiliate_link = affiliate_links[0].promotion_link
                logger.info(f"Affiliate link successfully created: {affiliate_link}")
                return affiliate_link

            logger.warning("AliExpress API returned no affiliate links")
            return None
        except Exception as e:
            logger.warning(
                "AliExpress API attempt %s/%s failed for %s: %s",
                attempt,
                API_RETRY_ATTEMPTS,
                original_link,
                e,
            )
            if attempt == API_RETRY_ATTEMPTS:
                logger.error("AliExpress API retries exhausted")
                return None
            await asyncio.sleep(API_RETRY_DELAY_SECONDS * attempt)
    return None


async def forward_message(event, updated_text):
    for attempt in range(1, TELEGRAM_RETRY_ATTEMPTS + 1):
        try:
            if event.message.media:
                await client.send_file(
                    TARGET_CHANNEL_ID,
                    event.message.media,
                    caption=updated_text or None,
                )
                return

            if updated_text:
                await client.send_message(TARGET_CHANNEL_ID, updated_text)
                return

            logger.info("Skipping empty message after processing")
            return
        except Exception as e:
            logger.warning(
                "Telegram send attempt %s/%s failed: %s",
                attempt,
                TELEGRAM_RETRY_ATTEMPTS,
                e,
            )
            if attempt == TELEGRAM_RETRY_ATTEMPTS:
                raise

            await reconnect_client()
            await asyncio.sleep(TELEGRAM_RETRY_DELAY_SECONDS * attempt)


async def reconnect_client():
    try:
        if client.is_connected():
            await client.disconnect()
    except Exception as e:
        logger.warning("Telegram disconnect before reconnect failed: %s", e)

    await asyncio.sleep(RECONNECT_DELAY_SECONDS)
    await start_client()


async def main():
    while True:
        try:
            await start_client()
            await client.run_until_disconnected()
            logger.warning(
                "Telegram disconnected. Reconnecting in %s seconds...",
                RECONNECT_DELAY_SECONDS,
            )
        except Exception as e:
            logger.error("Main loop error: %s", e)

        await asyncio.sleep(RECONNECT_DELAY_SECONDS)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main process error: {e}")
