Bulk user upload
================

We use the `/admin/utils/bulkuserupload/` utility when new users should have
specific publications associated with their user profile upon activation.
Examples:

* Reader has already paid for a publication (e.g. Deep pre-order, FJ
  Kickstarter backers)
* Basic Author needs manual onboarding
* Pro Author needs manual onboarding

Create a new batch user import
------------------------------

1.  Visit https://beta.publet.com/admin/utils/bulkuserupload/add/
2.  Give a `Name` so we know where this batch began (e.g. January FJ import)
3.  Use `Stripe id` as if it were a campaign name (e.g. fj-kickstarter-20)
4.  Select publications to be associated with this user upon activation. This
    creates `purchase` records.
5.  Paste `Csv data` in formate `first,last,email`
6.  Use `Message` to add custom activation email message for these users.
7.  Choose `Account type` option. *Readers* can only view output URLs.
    *Basic Author* can create publication of type identity. *Pro Author* users
    have no restrictions.
8.  Select any `Groups` that Basic or Pro Author users should have membership.
    Don't set for Reader users. Selected options will create `group member`
    records of type `collaborator` upon activation.
9.  Save.

Send activation emails
----------------------

1.  Visit https://beta.publet.com/admin/utils/useraccountrequest/
2.  Select the relevant user accounts. Usually these will have a red dot in
    the `Notified` column.
3.  Select the `Notify selected users by email` action option.
4.  Click `Go`.
