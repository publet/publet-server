Quality assurance
=================

Given our development workflow, only a single issue can be tested at a time.
This allows us to deploy new code more often.  You can read about the workflow
[here][workflow].

[workflow]: https://github.com/publet/publet/blob/master/docs/workflow.md

Steps
-----

1.  Go to the list of open pull requests in GitHub
2.  Find the one with the *Ready for QA* label
3.  Open it and follow the instructions for testing.
4.  Leave your comments and apply additional labels (*QA pass* or *QA fail*).

Pull requests labeled with *Queued* are finished in terms of code and are ready
for testing once the current issue is done being tested.
