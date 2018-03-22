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
import itertools
import struct
import socket


def mapcat(fn, iterable):
    return itertools.chain.from_iterable(itertools.imap(fn, iterable))


def flatten(coll):
    return list(itertools.chain.from_iterable(coll))


def merge(a, b):
    for k, v in b.items():
        if not v:
            continue

        a[k] = v

    return a


def some(pred, coll):
    """
    Return first logical true in coll, otherwise None
    """
    for el in coll:
        val = pred(el)

        if val:
            return val


def ip2int(addr):
    if not addr:
        return

    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


def get_in(obj, *keys):
    if not obj:
        return None

    for k in keys:
        v = obj.get(k, None)

        if not v:
            return None

        obj = v

    return obj
