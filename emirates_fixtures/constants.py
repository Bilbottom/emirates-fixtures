"""
Constants to be used in the project.
"""
import pathlib

#  General constants
ROOT = pathlib.Path(__file__).parent  # Resolves to emirates_fixtures/

#  Emirates constants
EMIRATES_WEBSITE = (
    "https://hospitality.arsenal.com/matchday-hospitality/arsenal-home-fixtures/"
)

#  Google Calendar constants
CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"
