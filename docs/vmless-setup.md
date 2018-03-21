VM-less setup
=============

If you don't like to mess around with Vagrant or VMware Fusion and would like
to install Publet straight to your machine, then this guide is for you.

Things you will need:

* Python and Pip (virtualenv is recommended) - [use this guide][python-guide]
* nodejs and npm
* postgresql
* wkhtmltopdf - [download a binary here][wkhtmltopdf]
* calibre - [download a binary here][calibre]
* sass - `gem install sass`

[python-guide]: http://docs.python-guide.org/en/latest/starting/install/osx/
[wkhtmltopdf]: http://wkhtmltopdf.org
[calibre]: http://calibre-ebook.com/download_osx


## Instructions
* Add the following entry to your `/etc/hosts` `127.0.0.1 publet.example.com`
* Set the `PUBLET_USE_VMLESS` environment variable to a non-empty string
    * E.g. `$ export PUBLET_USE_VMLESS=yes`
* Create a virtualenv and activate it
  * `$ virtualenv venv`
  * `$ source venv/bin/activate`
* Run `$ pip install -r requirements.txt`
    * You might get some errors at this point related to the PIL library
* Run `$ fab local_bower_install`
* Run `$ npm install`
* Run `$ postgres -D /usr/local/var/postgres`, then open a new terminal instance. Make sure you're still in the same directory and activate virtualenv again w/ `$source venv/bin/activate`
* Run `$ createuser —interactive`
* Run `$ createuser -s postgres`
* Run `$ createdb publet`
* Run `python manage.py migrate --settings=publet.settings_osx`
* Run `python manage.py createsuperuser --settings=publet.settings_osx`. You'll be asked to provide a name, email, and password. Input whatever you want your local login credentials to be.
* Run `python manage.py runserver --settings=publet.settings_osx`
* Open the app at `http://publet.example.com:8000`
* Go to the admin and create a group for yourself (since you are a superuser, a
  group member will be created automatically for you)

Tips and tricks
---------------

### manage.py

You might want to create a bash/zsh/fish alias for the `python manage.py <xxx>
--settings=publet.settings_osx` fiasco.

For bash, this would look like:

```bash
function pm {
    python manage.py $* --settings=publet.settings_osx
}
```

Put this in your `~/.bashrc` and source it.  Then you can simply run `pm
migrate` etc.

### Sass compilation

Sass compilation is done with the `bin/watch_all_scss` script.  You're more
than welcome to use your own method as long as the resulting css is the same
--- because it's really dumb to always be overwriting each other's css.

### sudo

Avoid using `sudo` whenever possible.  Installing pip, npm and gem requirements
shouldn't require superuser privileges.
