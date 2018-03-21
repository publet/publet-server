Quality assurance (QA) and preparing for a release
==================================================

1.  Go to GitHub issues for current milestone
2.  View closed issues
3.  Move relevant Trello cards (for closed issues) from the `Development`
    column to the `QA` column
4.  Create additional Trello cards in `QA` column for additional closed issues
5.  Hop into your terminal, change into Publet directory and
    `git pull origin master`
6.  Run `fab copy_beta_db_to_staging:<your production username>`
7.  Clean your browser cache (or burn your computer and buy a new one)
8.  Visit https://staging.publet.com/
9.  Do whatever tasks are necessary to determine if issue has been completed
10. Move completed cards from Trello `QA` column to `Production` column
11. Go to GitHub and open a pull request from `master` branch into `production`
    branch with title like "March 25 milestone QA'd and ready for deployment."
    (click on green pull request symbol on left side of bar. Choose base
    production)
12. Assign PR to Honza
13. Move any remaining GH sprint issues to the next sprint
14. Close the milestone

Publet's git-flow (abbreviated version):
----------------------------------------

1.  new code on feature branches
2.  master = git-flow's develop (working features that haven't been QAd)
    +continuous deployment to staging server
3.  production branch = git-flow's master (always reflecting the code on
    production server)

Modified from: http://nvie.com/posts/a-successful-git-branching-model/


Demo
----

1. https://vimeo.com/90458285 (pw: publet)
- simulations (1:30)
- themes (1:00)
- Git tour (1:36)
- PR (2:11)


Simulation testing (optional)
-------------------------------

1. Create simulation in /admin/ on staging with 1 or more publications
2. Review outputs for CSS and other irregularities
3. Create Trello tickets detailing formatting issues including URL and visuals.


Reporting bugs
--------------

When reporting a bug, please make sure that you provide as much detail as
possible, including:

* Steps to reproduce the issue (first thing a developer will do is try and
  reproduce it; only then can they begin to fix it)
* URLs
* Screenshots
* Screencasts - [licecap][1] is amazing
* Browser name and version if it's a frontend issue

If you spot a bug, please try and reproduce it a few times to make sure it's
not some temporary hiccup.  Also, before opening an issue, reproduce it on
staging --- chances are that the bug is only affecting beta but it's already
fixed on staging (meaning, opening a new ticket would be a waste of time).

[1]: http://www.cockos.com/licecap/
