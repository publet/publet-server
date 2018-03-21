# purescript-track

This is the new, experimental tracking javascript code.  It replaces our current
solution written in Angular and Bacon.js.  It's implemented in [purescript][1]
using an FPR style (ie using signals).


## hacking

* Install purescript
* Install [pulp][2]
* `$ pulp dep install`
* `$ pulp server`
* `open index.html`

[1]: http://www.purescript.org/
[2]: https://github.com/bodil/pulp

## building a dist

This can be done simply by running `make`.  The Makefile uses pulp's browserify
to optimize the code, and then it uses uglifyjs to compress, mangle and minify
the output.
