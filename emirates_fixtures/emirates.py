"""
Parse the Emirates website for the upcoming fixtures.
"""
from __future__ import annotations

import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

EMIRATES_WEBSITE = (
    "https://hospitality.arsenal.com/matchday-hospitality/arsenal-home-fixtures/"
)


def _from_friendly_date(friendly_date: str) -> datetime.datetime:
    """
    Convert a friendly date to a ``datetime.datetime`` object.

    A friendly date is a string that looks like:

        Sat Jan 1 2020 | Kick-Off 3:00 PM

    :param friendly_date: The friendly date to convert.

    :return: A ``datetime.datetime`` object.
    """
    pattern = "%a %b %d %Y %I:%M %p"

    return datetime.datetime.strptime(friendly_date.replace("| Kick-Off ", ""), pattern)


class Fixture:
    """
    Basic information on the fixture.
    """

    name: str
    date_time: datetime.datetime

    def __str__(self) -> str:
        return f"{self.name} - {self.date_time.isoformat()}"

    def __repr__(self) -> str:
        return f"Fixture(name='{self.name}', date_time={repr(self.date_time)})"

    def __init__(self, name: str, date_time: datetime.datetime):
        self.name = name
        self.date_time = date_time

    @classmethod
    def from_web_element(cls, web_element: WebElement) -> Fixture:
        """
        Create a fixture from a Selenium ``WebElement``.

        :param web_element: The Selenium ``WebElement`` to parse.

        :return: A fixture with basic information.
        """
        name, friendly_date = web_element.text.split("\n")[:2]

        return cls(name=name, date_time=_from_friendly_date(friendly_date))


def get_fixtures(secs_delay: int = 3) -> list[Fixture]:
    """
    Return the fixture information from the Emirates website.

    :param secs_delay: Number of seconds to wait before pulling the fixture
        information. This allows the page to load. Defaults to 3 seconds.
    """
    driver = webdriver.Chrome()
    driver.get(EMIRATES_WEBSITE)
    time.sleep(secs_delay)

    fixtures = driver.find_element(By.CLASS_NAME, value="tab_contents")

    return [
        Fixture.from_web_element(fixture)
        for fixture in fixtures.find_elements(By.TAG_NAME, value="li")
        if fixture.text
    ]
