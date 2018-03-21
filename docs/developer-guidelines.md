Developer guidelines
====================

* [Writing good commit messages][1]
* [Trailing whitespace][2] is [evil][3]
* Create database migrations on `master` only
* Use spaces instead of tabs
* If you find yourself in a painful workflow, please talk to Honza.  There
  might be a solution ready for you somewhere in the `fabfile` or in the `bin`
  directory.
* Don't check in editor-specific code or configurtion files
* Limit the number of dependencies as much as possible
* Write unittests as often as possible.  Write code that's easily testable.
  But at the same time, don't feel like we need 100% test coverage.  Don't
  write tests for the sake of writing tests.
* Write tests especially for data integrity code and to protect against
  regressions
* Don't be too clever.  Write code that's easy to understand.
* Boring technology is awesome.
* Automate

Python
------

* Try to adhere to [PEP8][4] as much as possible

Javascript
----------

* Make sure your code passes the jshint linter using our `.jshintrc`


[1]: http://robots.thoughtbot.com/5-useful-tips-for-a-better-commit-message
[2]: http://programmers.stackexchange.com/questions/121555/why-is-trailing-whitespace-a-big-deal
[3]: http://codeimpossible.com/2012/04/02/Trailing-whitespace-is-evil-Don-t-commit-evil-into-your-repo-/
[4]: http://legacy.python.org/dev/peps/pep-0008/
