from dotenv import load_dotenv
import os

load_dotenv()

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY")

OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")