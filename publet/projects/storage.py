import os
import posixpath

from django.conf import settings
from django.contrib.staticfiles.storage import CachedStaticFilesStorage
from django.utils.six.moves.urllib.parse import unquote


class PubletCachedStaticFilesStorage(CachedStaticFilesStorage):
    """
    This storage backend allows files fromm MEDIA_ROOT to be included inside a
    static file without raising an exception during collectstatic.

    As soon as Django detects a url of any sort, it assumes it's another static
    file.
    """

    def url_converter(self, name, template=None):
        """
        Returns the custom URL converter for the given file name.
        """
        if template is None:
            template = self.default_template

        def converter(matchobj):
            """
            Converts the matched URL depending on the parent level (`..`)
            and returns the normalized and hashed URL using the url method
            of the storage.
            """
            matched, url = matchobj.groups()
            # Completely ignore http(s) prefixed URLs,
            # fragments and data-uri URLs
            if url.startswith(('#', 'http:', 'https:', 'data:', '//',
                               settings.MEDIA_URL)):
                return matched
            name_parts = name.split(os.sep)
            # Using posix normpath here to remove duplicates
            url = posixpath.normpath(url)
            url_parts = url.split('/')
            parent_level, sub_level = url.count('..'), url.count('/')
            if url.startswith('/'):
                sub_level -= 1
                url_parts = url_parts[1:]
            if parent_level or not url.startswith('/'):
                start, end = parent_level + 1, parent_level
            else:
                if sub_level:
                    if sub_level == 1:
                        parent_level -= 1
                    start, end = parent_level, 1
                else:
                    start, end = 1, sub_level - 1
            joined_result = '/'.join(name_parts[:-start] + url_parts[end:])
            hashed_url = self.url(unquote(joined_result), force=True)
            file_name = hashed_url.split('/')[-1:]
            relative_url = '/'.join(url.split('/')[:-1] + file_name)

            # Return the hashed version to the file
            return template % unquote(relative_url)

        return converter
