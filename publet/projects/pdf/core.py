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
from functools import partial
from pyquery import PyQuery as pq
from lxml.etree import tostring


class Break(object):

    def __repr__(self):
        return 'Break'


class Bullet(object):

    def __repr__(self):
        return 'Bullet'


class Font(object):

    def __init__(self, font_id, family, color, size):
        self.font_id = font_id
        self.family = family
        self.color = color
        self.size = size


class Text(object):

    def __init__(self, text, font=None):
        self.text = text
        self.font = font

    def __repr__(self):
        return 'Text'

    def get_font_score(self):
        if not self.font:
            return

        return {
            'font': self.font.font_id,
            'score': len(self.text),  # Used for fonts
            'size': self.font.size
        }


class Photo(object):

    def __init__(self, filename):
        self.filename = filename

    def __repr__(self):
        return 'Photo <{}>'.format(self.filename)


BREAK = Break()
BULLET = Bullet()


def is_break(e):
    return e == BREAK


def neg(f):
    """
    Given a function, return a new function which returns the opposite
    of the original function
    """
    def g(*args, **kwargs):
        return not f(*args, **kwargs)
    return g


def split_at(pred, it):
    """
    Iterate over the iterable ``it``, splitting on an element when the
    predicate returns True.  Return a collection of collections.
    """
    colls = []
    temp = []

    for el in it:
        if pred(el):
            colls.append(temp)
            temp = []
        else:
            temp.append(el)

    if temp:
        colls.append(temp)

    return colls


def is_empty(el):
    if el.getchildren():
        return False

    if el.text in ['', ' ', None]:
        return True


def get_symbol_font_id(fonts):
    for f in fonts.values():
        if f.family == 'Symbol':
            return f.font_id


def make_is_symbol(symbol_font_id):
    def is_symbol(el):
        return el.attrib['font'] == symbol_font_id

    return is_symbol


def parse_page(fonts, page):
    result = []

    prev = None

    symbol_font_id = get_symbol_font_id(fonts)
    is_symbol = make_is_symbol(symbol_font_id)

    for page_child in page.getchildren():

        if page_child.tag == 'image':
            result.append(Photo(page_child.attrib['src']))

        if page_child.tag == 'text':
            if is_empty(page_child) and is_empty(prev):
                pass
            elif is_empty(page_child):
                result.append(BREAK)
            elif is_symbol(page_child):
                result.append(BULLET)
            else:
                attr = dict(page_child.attrib)
                children = page_child.getchildren()

                if children:
                    parts = [page_child.text]

                    for i in page_child.iterchildren():
                        parts.append(tostring(i))

                    parts.append(page_child.tail)

                    parts = filter(None, parts)
                    parts = filter(lambda x: x != '\n', parts)
                    text = ''.join(parts)
                else:
                    text = page_child.text

                attr.update(dict(text=text))
                result.append(attr)

        prev = page_child

    p_result = [None] + result[:-1]
    n_result = result[1:] + [None]

    doc = []

    in_bullet = False
    bullet = []

    def format_bullet(b):
        return '<li>{}</li>'.format(''.join(b).encode('utf8'))

    for r, p, n in zip(result, p_result, n_result):
        if r == BREAK and not in_bullet:
            doc.append(BREAK)

        if isinstance(r, Photo):
            doc.append(r)
            doc.append(BREAK)
            continue

        if r == BREAK and p == BULLET:
            if in_bullet:
                doc.append(format_bullet(bullet))
                bullet = []
            else:
                in_bullet = True

            continue

        if r not in [BREAK, BULLET]:

            if p and p not in [BREAK, BULLET]:
                if not isinstance(p, Photo):
                    if p['top'] and p['height']:
                        prev_bottom = int(p['top']) + int(p['height'])

                        if (int(r['top']) - prev_bottom) > 5:
                            if in_bullet:
                                in_bullet = False
                                doc.append(format_bullet(bullet))
                                bullet = []

                            doc.append(BREAK)

            if not in_bullet:
                doc.append(r)

        if r not in [BREAK, BULLET] and in_bullet:
            bullet.append(r['text'])

    groups = split_at(is_break, doc)

    elements = []

    for group in groups:
        if len(group) == 1 and isinstance(group[0], Photo):
            elements.append(group[0])
        else:
            if 'font' in group[0]:
                f = group[0]['font']
                font = fonts[f]

                text = ''.join([e['text'] for e in group])
                elements.append(Text(text, font))
            else:
                text = ''.join(group)
                elements.append(Text(text))

    return elements


def collect_fonts(doc):
    h = pq(doc)
    font_elems = h('fontspec')
    fonts = {}

    for f in font_elems:
        font = f.attrib
        font_obj = Font(
            font['id'],
            font['family'],
            font['color'],
            font['size']
        )

        fonts[font_obj.font_id] = font_obj

    return fonts


def get_default_font(articles, fonts):
    if len(fonts) == 1:
        return fonts.values()[0]

    scores = {}
    total_score = 0

    for article in articles:
        for block in article:
            if isinstance(block, Text):
                score = block.get_font_score()
                if not score:
                    continue

                total_score += score['score']

                if score['font'] in scores:
                    scores[score['font']] += score['score']
                else:
                    scores[score['font']] = score['score']

    s = scores.items()

    if not s:
        return

    s.sort(key=lambda x: x[1], reverse=True)

    if len(s) > 2:
        head, sub_head = s[:2]

        head_per = round(head[1] / (total_score / 100.0))
        sub_head_per = round(sub_head[1] / (total_score / 100.0))

        if head_per > 50 and (head_per - sub_head_per) > 20:
            default_font = fonts[head[0]]
            return default_font
    else:
        return fonts[s[0]]


def parse_pdf_from_xml(xml):
    """
    ``xml`` is the output of ``pdftohtml -xml``
    """
    doc = pq(xml)

    pages = doc('page')
    fonts = collect_fonts(doc)

    parse = partial(parse_page, fonts)
    articles = map(parse, pages)
    default_font = get_default_font(articles, fonts)

    return articles, default_font
