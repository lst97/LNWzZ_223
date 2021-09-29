"""Discord API module"""

import os
import json
import time

import requests

from dotenv import load_dotenv

from database import db
from utils.debug import dbg

load_dotenv()

LOG = dbg("[discordAPI]")


class api:
    """Provid API access to LNWzZ_Demo Discord server.

    The bot have administrative right to the Discord server,
    we only use it to generate server invite link for now.
    More detail for the API:
    https://discord.com/developers/docs/resources/channel#create-channel-invite

    Attributes:
        _token: Discord Bot token.
        _guild: Discord Server "LNWzZ_Demo" token.
        _url: API link for generate invite link.
        _header: Http post header.
    """

    def __init__(self, email: str) -> None:
        """Init necessary information to use Discord API

        All operation pointing to 882895138844729346 channel.

        Args:
            email (str): User email as identifier when using SQL.
        """
        self._token = os.getenv("DISCORD_TOKEN")
        self._guild = os.getenv("DISCORD_GUILD")
        self._url = f"https://discordapp.com/api/channels/{882895138844729346}"
        self._headers = {
            "Authorization": f"Bot {self._token}",
            "User-Agent": f"HTTP API \
                (Python Requests HTTP Library v{requests.__version__})",  # HTTPS API?
            "Content-Type": "application/json",
        }
        self._email = email

    def ivlink(self) -> bool:
        """Generate invite link only allowed one person with unlimited time.

        The link will be generated from Discord API.
        The function also update the database about the link.
        Prefix is exculded. (https://discord.gg/)

        Returns:
            bool:
                true: code successfully insert or update to the database.
                false: code cannot get from API or database operation failer.
        """

        for attempts in range(3):
            try:
                res = requests.post(
                    self._url + "/invites",
                    headers=self._headers,
                    data=json.dumps({"max_uses": 1, "unique": True, "max_age": 0}),
                )
                break

            except requests.exceptions.Timeout as ex:
                time.sleep(1)
                LOG.print(str(ex), status="warning")

                if attempts == 2:
                    LOG.print("API request timeout!", status="critical")
                    return False

        link = json.loads(res.text)["code"]
        LOG.print("Invite Generated.", status="info")

        # update to SQL
        database = db("sqlite3.db")
        return database.update_ivlink(self._email, link)

    @staticmethod
    def member_status() -> list:
        """Get online members count.

        Returns:
            list: Total count, Online count.
        """
        json_data = requests.get(
            "https://discord.com/api/guilds/882895138182033429/widget.json"
        ).json()
        member_list = []
        member_list.append(json_data["name"])
        member_list.append(len(json_data["members"]))

        return member_list
