import datetime
import time
from typing import Iterator

from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions

import feedparser
import dateutil.parser
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class FidoParser(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    def __init__(self,
                 refer: S3PRefer,
                 plugin: S3PPlugin,
                 restrictions: S3PPluginRestrictions,
                 web_driver: WebDriver):
        super().__init__(refer, plugin, restrictions)
        
        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        
    def _parse(self) -> None:
        ...

    def _latest_pubs(self) -> Iterator[S3PDocument]:
        # Parse the ECB RSS feed
        ecb_feed = feedparser.parse(self.RSS)

        # Iterate through feed entries
        for entry in ecb_feed.entries:
            parsed_date = dateutil.parser.parse(entry.published)
            yield S3PDocument(
                None,
                entry.title,
                entry.summary if 'summary' in entry else None,
                None,
                entry.link,
                None,
                None,
                parsed_date.replace(tzinfo=None),
                None,
            )