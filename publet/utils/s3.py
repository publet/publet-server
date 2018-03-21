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
