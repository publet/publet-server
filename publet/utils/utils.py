import json
import random
import os
import hmac
import hashlib
import base64
import string
from subprocess import check_output
from datetime import datetime, timedelta
from contextlib import contextmanager
from cStringIO import StringIO
import psutil

import requests
from PIL import Image
from mobiledetect import MobileDetect
from django.conf import settings
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string


FILEPICKER_SECRET = getattr(settings, 'FILEPICKER_SECRET', '')
FILEPICKER_API_KEY = getattr(settings, 'FILEPICKER_API_KEY', '')
HOST = getattr(settings, 'HOST', None)
PREVIEW_URL = getattr(settings, 'PREVIEW_URL', None)
VARNISH_PURGE_PORT = getattr(settings, 'VARNISH_PURGE_PORT', None)
VARNISH_PURGE_SECRET = getattr(settings, 'VARNISH_PURGE_SECRET', None)

RANDOM_STRING_CHARS = string.lowercase + string.digits


def years(n):
    return n * 365


def int_to_string(n):
    if n < 0 and n > 99:
        return

    if not isinstance(n, int):
        return

    dictionary = {
        0: 'zero',
        1: 'one',
        2: 'two',
        3: 'three',
        4: 'four',
        5: 'five',
        6: 'six',
        7: 'seven',
        8: 'eight',
        9: 'nine',
        10: 'ten',
        11: 'eleven',
        12: 'twelve',
        13: 'thirteen',
        14: 'fourteen',
        15: 'fifteen',
        16: 'sixteen',
        17: 'seventeen',
        18: 'eighteen',
        19: 'nineteen',
        20: 'twenty',
        30: 'thirty',
        40: 'forty',
        50: 'fifty',
        60: 'sixty',
        70: 'seventy',
        80: 'eighty',
        90: 'ninety'
    }

    v = dictionary.get(n, None)

    if v:
        return v

    try:
        return dictionary[n - n % 10] + '-' + dictionary[n % 10]
    except KeyError:
        return


def get_random_string(length=5):
    chars = [random.choice(RANDOM_STRING_CHARS) for i in xrange(length)]
    return ''.join(chars)


def send_welcome_email(user, request, **kwargs):
    account_type = user.account_type

    kwargs = {
        'HOST': HOST,
        'user': user,
        'account_type': account_type
    }

    if user.is_reader:
        from publet.projects.models import Publication
        free = Publication.objects.filter(
            price__isnull=True, status='live')[:5]
        newest = Publication.objects.order_by('-modified')[:5]

        kwargs.update({
            'free': free,
            'newest': newest
        })

    else:
        groups = user.get_groups()

        kwargs.update({
            'groups': groups
        })

    message = render_to_string('welcome_email.html', kwargs)

    user.email_user('Welcome to Publet', message)


def slugify_with_hash(value, *args, **kwargs):
    suffix = get_random_string()
    base = slugify(value)[:249]
    return ''.join([base, '-', suffix])


def slugify_uniquely(value, model, slugfield="slug"):
    suffix = 0
    potential = base = slugify(value)[:255]

    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not model.objects.filter(**{slugfield: potential}).count():
            return potential
        suffix += 1


def get_filepicker_policy(override=None, delta=None):
    if not delta:
        delta = timedelta(days=7)

    future = datetime.utcnow() + delta
    future_epoch = int(future.strftime('%s'))

    calls = ['pick', 'read', 'stat', 'write', 'writeUrl', 'store', 'convert']

    if override:
        calls = override

    policy = {
        'expiry': future_epoch,
        'call': calls
    }

    policy = json.dumps(policy)
    policy = base64.urlsafe_b64encode(policy)

    signature = hmac.new(FILEPICKER_SECRET, policy, hashlib.sha256).hexdigest()

    return policy, signature


def get_filepicker_read_policy(delta=None):
    future = datetime(2050, 1, 1, 12, 0, 0)
    future_epoch = int(future.strftime('%s'))

    policy = json.dumps(dict(call=['read', 'convert'], expiry=future_epoch))
    policy = base64.urlsafe_b64encode(policy)

    signature = hmac.new(FILEPICKER_SECRET, policy, hashlib.sha256).hexdigest()

    return policy, signature


def upload_file_to_filepicker(path):
    if not os.path.exists(path):
        raise Exception('File not found')

    policy, signature = get_filepicker_policy()

    url = ('https://www.filepicker.io/api/store/S3?key={}'
           '&signature={}&policy={}')

    url = url.format(FILEPICKER_API_KEY, signature, policy)

    files = {'fileUpload':  open(path, 'rb')}
    r = requests.post(url, files=files)

    if r.status_code == 200:
        return r.json()


@contextmanager
def cd(path):
    pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(pwd)


def get_image_dimensions(url):
    """
    Return a tuple of (w, h) in pixels
    """
    r = requests.get(url, verify=False)

    if r.status_code != 200:
        raise Exception('Failed to download {}'.format(url))

    f = StringIO(r.content)
    image = Image.open(f)

    return image.size


def chmod_recursive(path, perms):
    """
    Perms should be octal, eg 0775
    """
    for root, dirs, files in os.walk(path):

        for d in dirs:
            os.chmod(os.path.join(root, d), perms)

        for f in files:
            os.chmod(os.path.join(root, f), perms)


def get_disk_stats():
    out = check_output('df | grep "/$"', shell=True)
    name, size, avail, used, perc = filter(None, out.split(' '))[:-1]

    return {
        'name': name,
        'size': int(size),
        'available': int(avail),
        'used': int(used),
        'used_percent': int(perc.replace('%', ''))
    }


def get_cpu_usage():
    return psutil.cpu_percent()


class DatetimeJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def purge_in_varnish(filename):
    url = "{}:{}".format(PREVIEW_URL, VARNISH_PURGE_PORT)

    if not filename.startswith('/'):
        filename = '/' + filename

    if filename.endswith('index.html'):
        filename = filename[:-10]

    data = filename
    headers = {
        'x-publet-auth': VARNISH_PURGE_SECRET
    }
    r = requests.post(url, headers=headers, data=data)

    if r.status_code > 399:
        raise Exception('Failed purge {}'.format(filename))


def pretty_print_json(obj_or_str):
    if not isinstance(obj_or_str, object):
        obj_or_str = json.loads(obj_or_str)

    print json.dumps(obj_or_str, indent=4)


def font_to_font_face(f):
    css = []
    local = f['fontFamily'].split(',')[0].strip('"\' ')

    font_face = []
    url = f.get('url', None)

    if not url:
        return ''

    data = {
        'font-family': '"%s"' % local,
        'font-style': f.get('fontStyle', 'normal'),
        'src': 'local("{}"), url("{}") format("woff2")'.format(local, url)
    }

    for k, v in data.items():
        font_face.append('    {}: {};'.format(k, v))

    body = '\n'.join(font_face)
    css.append('@font-face {\n%s\n}' % body)

    return '\n\n'.join(css)


def sha1_string(s):
    return hashlib.sha1(s.encode('utf8')).hexdigest()


def user_agent_to_device(ua):
    md = MobileDetect(useragent=ua)
    if md.is_phone():
        return 'phone'
    elif md.is_tablet():
        return 'tablet'
    else:
        return 'desktop'
