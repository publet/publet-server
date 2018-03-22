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
from mimetypes import guess_type
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings


AWS_ACCESS_KEY_ID = getattr(settings, 'AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getattr(settings, 'AWS_SECRET_ACCESS_KEY')


def get_bucket(name):
    c = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    return c.get_bucket(name)


def upload_file_to_s3(bucket_name, content, filename, mimetype=None):
    bucket = get_bucket(bucket_name)

    if not mimetype:
        mimetype, _ = guess_type(filename)

    k = Key(bucket)
    k.key = filename

    if mimetype:
        k.content_type = mimetype

    k.set_contents_from_string(content, policy='public-read')
