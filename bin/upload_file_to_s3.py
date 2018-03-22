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
import sys
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from raven import Client


S3_ACCESS_KEY = 'AKIAIU5WCE4LRFUSLMSA'
S3_SECRET_KEY = '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'

DSN = ('https://947c8d50eea04f66a23fbb672ad7a391:'
       'bbd7c3c285d043d7a3e4fc859d025e70@app.getsentry.com/9083')


client = Client(DSN)


def get_bucket(name):
    c = S3Connection(S3_ACCESS_KEY, S3_SECRET_KEY)
    return c.get_bucket(name)


def main(bucket_name, filename):
    bucket = get_bucket(bucket_name)

    k = Key(bucket)
    k.key = os.path.basename(filename)
    k.set_contents_from_filename(filename)


if __name__ == '__main__':
    try:
        if len(sys.argv) < 3:
            print 'Not enough args specified'
            print 'upload_file_to_s3 <bucket> <filename>'
            raise Exception('not enough args')

        main(sys.argv[1], sys.argv[2])
    except Exception:
        client.get_ident(client.captureException())
        sys.exit(1)
