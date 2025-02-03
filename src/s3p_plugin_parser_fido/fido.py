import datetime
from typing import Iterator

from s3p_sdk.exceptions.parser import S3PPluginParserOutOfRestrictionException
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions

import feedparser
import dateutil.parser
from s3p_sdk.types.plugin_restrictions import FROM_DATE


class FidoParser(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    def __init__(self,
                 refer: S3PRefer,
                 plugin: S3PPlugin,
                 restrictions: S3PPluginRestrictions,
                 feeds: list[str],
                 rss_only: bool = False,
                 ):
        super().__init__(refer, plugin, restrictions)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._rss_only = rss_only
        self.feeds = feeds

    def _parse(self) -> None:
        # TODO: remove this after implementing Additional Parser logic
        if not self._rss_only:
            raise NotImplementedError('RSS only mode available')

        # Allocating restrictions at feeds
        if isinstance(self._restriction.maximum_materials, int):
            if self._restriction.maximum_materials // len(self.feeds) >= 2:
                number = self._restriction.maximum_materials // len(self.feeds) + 1
            else:
                number = self._restriction.maximum_materials
        else:
            number = None

        # Iterating each feed
        for url in self.feeds:
            for document in self._slices(
                self._feed(url),
                number
            ):
                # Additional Parser logic here
                document.loaded = datetime.datetime.now().replace(microsecond=0)
                # ===

                try:
                    self._find(document)
                except S3PPluginParserOutOfRestrictionException as e:
                    if e.restriction == FROM_DATE:
                        break

    def _slices(self, feed: Iterator[S3PDocument], number: int | None = None) -> Iterator[S3PDocument]:
        for current, element in enumerate(feed):
            if number is not None and current >= number:
                break
            yield element

    def _feed(self, url: str) -> Iterator[S3PDocument]:
        # Parse the RSS feed
        feed = feedparser.parse(url)

        # Iterate through feed entries
        for entry in feed.entries:
            # Publication date
            parsed_date = dateutil.parser.parse(entry.published)

            # Authors
            authors = []
            if entry.authors and len(entry.authors) > 0:
                for author in entry.authors:
                    authors.append(author.name)

            # Tags
            tags = []
            if entry.tags and len(entry.tags) > 0:
                for tag in entry.tags:
                    tags.append(tag.term)

            # Assembling and return document
            yield S3PDocument(
                None,
                entry.title,
                entry.summary if 'summary' in entry else None,
                None,
                entry.link,
                None,
                {
                    'authors': authors if authors else None,
                    'tags': tags if tags else None,
                },
                parsed_date.replace(tzinfo=None),
                None,
            )
