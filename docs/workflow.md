Development
===========

Publet uses [GitHub Flow](https://guides.github.com/introduction/flow/) as its
development workflow.  Master is always ready for production.  When your code
is ready to be reviewed, push it to staging.  Once it's approved, merge your PR
and deploy to production.

Branching
---------

Use GitHub issue numbers for feature branch names.  For example,
`feature/1361`.  Prepend commit messages with the issue number, like:

```
[#1361] Add 'body' to flavor name

Rest of your commit message
```

If you'd like to have the issue number automatically added, add these two files
and make sure they are both executable:

First, `.git/hooks/prepare-commit-msg`:

```sh
#!/bin/sh

branch=$(git rev-parse --abbrev-ref HEAD)
.git/hooks/format-commit-message.py $1 $branch
```

Second, `.git/hooks/format-commit-message.py`:

```python
#!/usr/bin/env python

import sys


def main():
    message_filename = sys.argv[1]
    branch = sys.argv[2]
    message = open(message_filename).read()

    if 'feature' in branch:
        issue_number = branch.split('/')[1]
        text = '[#{}]\n'.format(issue_number)
    else:
        text = ''

    message = text + message

    with open(message_filename, 'w') as f:
        f.write(message)


if __name__ == '__main__':
    main()
```

You use use `fab copy_beta_db_to_local:<your production username>` to get
real data into staging environment for demos, testing and QA.


Deployment
==========

Production
----------

    $ fab beta:<your username> deploy

Staging
-------

And any new environments

    $ fab staging:<your username> deploy

Maintenance mode
================

Beta
----

Enable maintenance mode:

    $ fab lb:<your username> enable_maintenance:beta

Disable maintenance mode:

    $ fab lb:<your username> disable_maintenance:beta

Staging
-------

Enable maintenance mode:

    $ fab lb:<your username> enable_maintenance:staging

Disable maintenance mode:

    $ fab lb:<your username> disable_maintenance:staging
