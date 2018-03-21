Installation
============

When developing Publet, we use a VM-oriented process.  The developer
environment and dependencies are all installed into a local VM.  The VM is
usually provided by VirtualBox or VMware Fusion, and it automatically
provisioned using saltstack.  This gives us the advantage of having the same
environment across the development team, and even our servers.  If your
development machine is underpowered, you may try to use our
[vmless setup][vmless].  This document will guide through the installation
process.

[vmless]: https://github.com/publet/publet/blob/master/docs/vmless-setup.md

First install the dependencies [Vagrant][1], [Virtualbox][2], [Fabric][3] and
[Bower][4].  Vagrant and Virtualbox have native installers, just download those
and run them.  Fabric is an automation tool written in Python and it can be
installed with `pip install fabric requests`.  Bower is a Javascript
package manager for the browser written in Node.js and it can be installed with
`npm install -g bower`.

* Clone and cd into the repo directory.
* First configure `settings_local.py` as described in the "Settings" section below.
* `$ pip install fabric requests`
* `$ fab bootstrap`
* Add `127.0.0.1 publet.example.com` to your `/etc/hosts` file
* `$ vagrant ssh`
* `(in vagrant) $ run`
* Open browser to http://publet.example.com:8080

This process will download the Ubuntu 12.04 64bit vagrant base box, import it
for you and boot up a VM.  It will then log into it and install Saltstack.
Saltstack is a configuration manager which we use to automatically set up our
server.  Once Saltstack is installed, we run it to bootstrap the vagrant VM.
The bootstrapping process itself installs nginx, postgresql, wkhtmltopdf,
calibre, etc.

Eventually it will get to the `Creating the superuser...` phase and
ask you to create a Username and Password for use with the admin.
Make sure to remember what you enter here!

Once that is done, you can log into the vagrant VM and run the
`run` command which is just a glorified `python manage.py runserver`.

[1]: http://www.vagrantup.com/
[2]: https://www.virtualbox.org/
[3]: http://docs.fabfile.org/en/1.7/
[4]: http://bower.io/

Settings
--------

When developing locally, create a file called `publet/settings_local.py` and
set the `FILEPICKER_API_KEY`, `POSTMARK_API_KEY`, `STRIPE_PUBLISHABLE_KEY` and
`STRIPE_SECRET_KEY` to your own development keys. You can use our shared
[local-only keys](https://github.com/publet/publet/wiki/Local-3rd-party-keys)

Create initial data
-------------------

Once you're running, log in to [publet.example.com:8080] with your
Superuser account. Then go to [/admin/] and then change type in the
[User profiles] for your account from reader to `pro`.

Now you can visit [/groups/] to create a group and then get to dev.

[publet.example.com:8080]: http://publet.example.com:8080/
[/admin/]: http://publet.example.com:8080/admin/
[/groups/]: http://publet.example.com:8080/groups/
[User Profiles]: http://publet.example.com:8080/admin/utils/userprofile/

Media compilation
-----------------

The `base.html` template has support for [LiveReload](http://livereload.com/)
built in, but you don't need to use this if you don't want to. When compiling
the CSS, use the `compressed` SCSS output style.

You can also use a CLI-based solution.  Install the sass gem and then:

    $ ./bin/watch_all_scss

Or if you want to simply compile once:

    $ ./bin/compile_site_css

