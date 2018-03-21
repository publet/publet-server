from django.db import models


class FilePickerField(models.CharField):

    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 255

        super(FilePickerField, self).__init__(*args, **kwargs)
