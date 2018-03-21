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
