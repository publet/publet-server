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
"""
December 2, 2013
December 02, 2013
december 2, 2013
december 02, 2013

Dec 2, 2013
Dec 02, 2013
dec 2, 2013
dec 02, 2013

2013-12-02
2013/12/02
2013.12.02

02-12-2013
02/12/2013
02.12.2013

12-02-2013
12/02/2013
12.02.2013
"""
import re


months = [
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december'
]

months_abbr = map(lambda x: x[:3], months)


def make_month_dict():
    d = {}

    c = 1

    for m, mm in zip(months, months_abbr):
        d[m] = c
        d[mm] = c
        c += 1

    return d

month_dict = make_month_dict()


# 2013-12-02
# 2013-12-2
# 2013/12/02
# 2013/12/2
# 2013.12.02
# 2013.12.2
d1_re = re.compile(
    r'\.*'
    r'(?P<year>\d{4})'
    r'[\-|/\.]'
    r'(?P<month>\d{1,2})'
    r'[\-|/\.]'
    r'(?P<day>\d{1,2})'
    r'\.*'
)


# December 2, 2013
# December 02, 2013
# december 2, 2013
# december 02, 2013
# Dec 2, 2013
# Dec 02, 2013
# dec 2, 2013
# dec 02, 2013
d2_re = re.compile(
    r'\.*'
    r'(?P<month>%s)'
    r' (?P<day>\d{1,2})'
    r', (?P<year>\d{4})\.*' % '|'.join(months + months_abbr),
    flags=re.IGNORECASE
)

# 12/2/2013
# 12-2-2013
# 12.2.2013
# 12/02/2013
# 12-02-2013
# 12.02.2013
d3_re = re.compile(
    r'\.*'
    r'(?P<month>\d{1,2})'
    r'[\-|/\.]'
    r'(?P<day>\d{1,2})'
    r'[\-|/\.]'
    r'(?P<year>\d{4})'
    r'\.*'
)


def find_dates(html):
    matches = list(d1_re.finditer(html)) \
        + list(d2_re.finditer(html)) \
        + list(d3_re.finditer(html))

    for m in matches:
        g = m.groupdict()

        if len(g['month']) > 2:
            g['month'] = month_dict[g['month'].lower()]

        yield g
