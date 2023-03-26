from dotenv import load_dotenv
import os
import logging


# Load .env file
load_dotenv()
ENV_URL_SERVICE_RESOURCES = os.getenv('ENV_URL_SERVICE_RESOURCES')
ENV_DEBUG = os.getenv('ENV_DEBUG')
ENV_LOGGING_LEVEL = eval(str(os.getenv('ENV_LOGGING_LEVEL')))