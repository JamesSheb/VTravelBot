import os

from dotenv import load_dotenv


load_dotenv()

# your bot token from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')

# your headers from environment variables
HEADERS_BOT = os.getenv('HEADERS_BOT')
HEADERS_TRANSLATOR = os.getenv('HEADERS_TRANSLATOR')
