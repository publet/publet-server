Adding custom permissions
=========================

First of all, you should add the permission to the `Meta` class of the
permission's model:

``` python
class Theme(models.Model):
    ...

    class Meta:
        permissions = (
            ('update_theme_on_disk', 'Update theme on disk',),
        )
```

This should usually be enough but because we're using South to manage database
migrations, we have some extra work to do.

Next, create a data migration for the app in which your model is found.  In our
case, the `projects` app.

```
$ python manage.py datamigration projects add_custom_permission --freeze=content-types --freeze=auth
```

The freeze flags are super important.  They tell South to include the content
type and auth apps' models in the giant dict at the bottom of the migration
file.

Next, open up the newly created migration file and implement the `forwads`
method.  Don't forget to use the `orm` object for referring to models.

``` python
def forwards(self, orm):
    ct = orm['contenttypes.ContentType'].objects.get(app_label='projects',
                                                     model='theme')
    orm['auth.Permission'].objects.create(codename='update_theme_on_disk',
                                          name='Update theme on disk',
                                          content_type=ct)
```

Finally, you can run the `migrate` command.
