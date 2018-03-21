How to write an awesome ticket
==============================

*Or, how to make an engineer love you*

General
-------

If you are reporting a bug, give the engineer as much information as you
possibly can.  Strive to answer the following questions:

* __What did I expect to happend and what happened instead?__
* What exact steps will reproduce the issue?
* Where did it happen?  (Beta vs staging)
* What is the URL where it happened?
* Was I logged in or anonymous?
* When did I first notice it?
* Would a screenshot help explain what I mean?

For example, if you open a new ticket with a title of *EDITOR: broken* and a
description of *The editor is broken*, the engineer will most likely curse
under their breath and promptly close the ticket.

Additional tips
---------------

* Use prose, write full sentences, use paragraphs to separate thoughts
* Never edit a ticket's description after it's been created.  Comment freely.
* Create smaller, more focused tickets instead of big ones with many items
* Reference tickets with `#xyz` where `xyz` is an issue number in GitHub
* Use consistent naming for things (e.g. don't call something an image in one
    sentence and a photo in another)
* Try to think about what will make this ticket *done* (e.g. "improve editor"
    isn't helpful)
* Avoid adding new tickets to the current sprint most of the time
* Instead of prefixing the ticket's title with a word which denotes a category,
    use a label (e.g. *EDITOR: add social links* should be *Add social links*
    with a label of *editor*)
* Avoid creating too many labels.  Reuse if possible.  (e.g. instead of
    creating a new label for each client, tag them all with *client*)
* Check GitHub regularly for comments on tickets that you created
* Resist the urge to label everything *high priority*

Workflow
--------

* Create ticket
* Add label and milestones as necessary
* Assign to an engineer
* The assigned engineer will make every effort to do an initial review of the
    ticket as soon as possible to determine if
    * its urgency is accurate
    * it contains enough information to start work
    * it should be assigned to someone else
* If the ticket needs more information, questions will be asked and the ticket
    will be reassigned back to its author.
* Once the ticket author supplies the missing information, the ticket should be
    assigned back to the engineer.  This allow us to quickly check a queue, as
    it were, of work that needs to be addressed.  Once there are no more
    tickets in the current sprint assigned to you, you know you are done.
