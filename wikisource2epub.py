import io
import re
import urllib.parse

import ebooklib.epub
import mwparserfromhell
import requests


URL_PATTERN = re.compile('https?://([a-z-]+)\.wikisource\.org/wiki/(.+)', re.IGNORECASE)
API_URL = 'https://{}.wikisource.org/w/api.php'.format
BASE_ARGS = {
    'format': 'json',
    'redirects': '1',
}
QUERY_ARGS = dict(BASE_ARGS, **{
    'action': 'query',
    'prop': 'revisions',
    'rvprop': 'content',
})
PARSE_ARGS = dict(BASE_ARGS, **{
    'action': 'parse',
})


class Page(object):

    MAX_DEPTH = 1

    def __init__(self, title, lang=None, max_depth=MAX_DEPTH):
        url_match = URL_PATTERN.match(title)
        if URL_PATTERN.match(title):
            self._lang, self._title = url_match.groups()
        else:
            self._lang = lang
            self._title = title
        assert self._lang, 'Please specify lang'
        self._title = urllib.parse.unquote(self._title)
        self._data_query = None
        self._data_parse = None
        self._max_depth = max_depth

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def __repr__(self):
        return self.title

    @property
    def _page(self):
        if self._data_query is None:
            url = API_URL(self._lang) + '?' + urllib.parse.urlencode(dict(QUERY_ARGS, titles=self._title))
            self._data_query = requests.get(url).json()
        return list(self._data_query['query']['pages'].values())[0]

    @property
    def id(self):
        return self._page['pageid']

    @property
    def title(self):
        return self._page['title']

    @property
    def links(self):
        for link in self.wiki.filter_wikilinks():
            yield str(link.title)

    @property
    def content(self):
        return self._page['revisions'][0]['*']

    @property
    def wiki(self):
        return mwparserfromhell.parse(self.content)

    @property
    def html(self):
        if self._data_parse is None:
            url = API_URL(self._lang) + '?' + urllib.parse.urlencode(dict(PARSE_ARGS, page=self._title))
            self._data_parse = requests.get(url).json()
        return self._data_parse['parse']['text']['*']

    def _iter_all_pages(self, skip, depth):
        if depth > self._max_depth or self in skip:
            return

        yield self
        skip.add(self)
        for title in self.links:
            for page in Page(title, self._lang)._iter_all_pages(skip, depth + 1):
                yield page

    @property
    def all_pages(self):
        yield from self._iter_all_pages(set(), 0)

    def create_epub(self, file):
        book = ebooklib.epub.EpubBook()
        book.set_language(self._lang)
        book.set_title(self.title)

        for page in self.all_pages:
            uid = '%s.html' % page.id
            book.add_item(ebooklib.epub.EpubHtml(
                title=self.title, file_name=uid, uid=uid, content=page.html))
            book.spine.append(uid)

        book.add_item(ebooklib.epub.EpubNcx())
        ebooklib.epub.write_epub(file, book, {})


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Convert wikisource to epub.')
    parser.add_argument('url', type=str, help='wikisource url')
    buffer = io.BytesIO()
    Page(parser.parse_args().url).create_epub(buffer)
    sys.stdout.buffer.write(buffer.getvalue())
