"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from readability.readability import Document
from html2text import html2text
import misaka
from dateparse import find_dates


class PubletRenderer(misaka.HtmlRenderer):

    def __init__(self, *args, **kwargs):
        super(PubletRenderer, self).__init__(*args, **kwargs)
        self.images = []

    # Block level

    def block_code(self, code, language):
        return code

    def block_quote(self, quote):
        return quote

    def block_html(self, raw_html):
        return raw_html

    def header(self, text, level):
        return text

    def hrule(self):
        return ''

    def list(self, contents, is_ordered):
        return contents

    def list_item(self, text, is_ordered):
        return text

    def paragraph(self, text):
        return text

    def table(self, header, body):
        return body

    def table_row(self, content):
        return content

    def table_cell(self, content, flags):
        return content

    # Span level

    def autolink(self, link, is_email):
        return link

    def codespan(self, code):
        return code

    def double_emphasis(self, text):
        return '<b>{}</b>'.format(text)

    def emphasis(self, text):
        return '<i>{}</i>'.format(text)

    def image(self, link, title, alt_text):
        self.images.append(link.replace('\n', ''))
        return ''

    def linebreak(self):
        return ''

    def link(self, link, title, content):
        return ' <a href="{}">{}</a> '.format(
            link.replace('\n', ''), content)

    def raw_html(self, raw_html):
        return raw_html

    def triple_emphasis(self, text):
        return text

    def strikethrough(self, text):
        return text

    def superscript(self, text):
        return text


def filter_paragraph(p):
    if p == '':
        return False

    if p.startswith('#'):
        return False

    return True


def get_paragraphs(text):
    """
    Return a list of paragraphs from the ``text``.
    Ignore leading heading.

    ``text`` is a markdown string
    """
    paragraphs = text.split('\n\n')
    paragraphs = filter(filter_paragraph, paragraphs)

    images = []
    rendered = []

    for p in paragraphs:
        r = render_stripped_down_markdown(p)
        rendered.append(r['text'])
        images.append(r['images'])

    return rendered, images


def parse_with_readability(html):
    """
    Return

        {
            'title': '',
            'summary': ''
        }
    """
    doc = Document(html)
    return {
        'title': doc.short_title(),
        'summary': doc.summary(html_partial=True)
    }


def render_stripped_down_markdown(text):
    renderer = PubletRenderer()
    markdown = misaka.Markdown(renderer)
    result = markdown.render(text)

    return {
        'text': result,
        'images': renderer.images
    }


def parse_with_html2text(html):
    return html2text(html.encode('ascii', 'ignore'))


def parse_html(html):
    """
    Return

        {
            'title': '',
            'summary': '',
            'paragraphs': [],
            'dates': []
        }
    """
    doc = parse_with_readability(html)
    markdown = parse_with_html2text(doc['summary'])
    doc['paragraphs'], doc['images'] = get_paragraphs(markdown)
    doc['dates'] = list(find_dates(html))
    return doc
