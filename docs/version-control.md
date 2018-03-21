Version control specification
=============================

Publet users want to have the ability to roll back a publication to a previous
state.  Similar to Google Drive documents, they want to see a list of revisions
with timestamps and author names.  The user should be able to select one of the
revisions from the list and revert the publication to it.

Therefore, the publication needs to become an immutable data structure.  Each
modification of the publication's content will have to result in a new
publication instance being created in the database.  This will affect every
model that is *under* the publication, ie articles, sections, columns, blocks,
etc.  The head of each tree will be a new model, called `PublicationVersion`.
The original `Publication` model will point to a `PublicationVersion` instance.
Reverting to an old instance will only require us to change this pointer.

Listing revisions is as simple as listing the `PublicationVersion` instances
for that publication.  Previewing an old publication version is trivial.

This mechanism will produce many instances over time.  To preserve space, we
could do two things:

1.  Implement a policy that says that any edits older than 30 days will be
    deleted.
2.  Implement a [structural sharing of trees][1].

The second option is much more difficult.  This can be delayed until space and
or query time becomes an issue.

Implementation
--------------

The basic idea is that each publication-related operation will be done through
a single function.  This function will be responsible for copying the original
tree inside a database transaction and moving the current publication version
pointer.

Only the new-style publications (which include sections and columns) will be
supported.

Editor integration
------------------

TODO

[1]: http://hypirion.com/musings/understanding-persistent-vector-pt-1
