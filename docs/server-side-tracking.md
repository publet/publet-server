Server-side tracking
====================

Server-side tracking is now live on beta (2015-01-12).  As soon as the HTML
preview of a publication is requested, we record some basic information about
the request:

* IP address
* User agent
* Referrer and possible social referrer
* Time
* Anonymous ID or User ID if logged in

The anonymous ID works as follows:

1.  A user comes to the URL
2.  We generate a random uuid and store it in their session
3.  If they come back, we check if they have an anonymous ID in their session
4.  If they do, we store it; if not, we go to 2.

This allows us to present the following metrics (on the publication's data
page):

* Number of HTTP requests to the publication
* Number of unique server-side visitors

We don't need to rely on the page fully loading, javascript being executed or
the user leaving to record this information.
