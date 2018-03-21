Analytics.js
============

Publet is using the amazing [Analytics.js][1] library.  It only enables a
single, custom integration called *Publet*.  This document describes how to
build a release version of the library.

[1]: https://github.com/segmentio/analytics.js

Building
--------

First, in the root directory of the Publet project, clone the Analytics.js
repository.

    $ git clone git@github.com:segmentio/analytics.js.git analytics.js

Second, `cd` into it and install the required node modules

    $ npm install

Third, apply the Publet patch

    $ git apply ../analytics/publet-analytics.patch

Fourth, build the minified library

    $ make analytics.min.js


Changes
-------

If you'd like to upgrade the library itself or make changes to the integration,
feel free to do so.  Once you've made your changes, make sure to build the
library and replace the `publet/static/js/analytics.min.js` file with your new
file and commit it.
