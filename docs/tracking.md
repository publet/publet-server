# How it works

* User visits a Publet publication
* If this is their first time, we generate a unique `anonymous_id` for them and
  set it in their cookie.
* While they use the site, we track their engaged seconds and percent read.
* When they're ready to leave and navigate away or close the tab, we send the
  collected data to the server.
* If the user has a Publet account, we also collect their Publet user id.

# Beware

* Whitelist Publet in your adblocker of choice (Adblock, ghostery, disconnect)
* Publet respects the DNT setting in your browser.
* Publet does not track you when you are viewing your own publications.
* The local dev environment will override your DNT setting to always track but
  staging or beta will not.

# Data collected

## Event types

* Page view
* Engaged publication seconds
* Engaged article seconds
* Engaged block seconds
* Percent read publication
* Percent read article
* Server pageview

## Event fields

* created
* type
* user id
* anonymous id
* publication id
* article id
* block id
* block type
* seconds
* percent read
* url
* referrer
* social referrer
* ip address
* user agent
* user languages

## Geolocation

The user's IP address can be resolved to a location.  Each event has the
following location fields:

* continent
* country
* region (California, Ontario, etc)
* city

We are able to filter tracking events based on these fields.

# Visualizations

Visualizations are divided into tabs on the data page.  The tabs are
*audience*, *channel*, *content*, *reader* and *export*.

## Audience

### Impressions

Number of non-unique page views within the last 30 days.  E.g. you arrive at a
page, reload it and then leave.  This is 2 page views.

### Unique visitors

Number of unique visitors to the publication within the last 30 days.

### Conversion count

Number of times a Publet gate has been filled out and submitted in the last 30
days.

### Sessions

Number of user sessions in the last 30 days.  A session is a period of time
during which a person uses the site.  Once we detect a period of inactivity for
30mins, we conclude their session and start a new one.

### Engaged time

Total amount of time that users have spent engaging with an article within the
last 30 days.  A user is said to be engaged with a publication when they have
performed at a single action during the last 4mins.  This action could be
scrolling, moving the mouse, focusing, touching the screen, etc.

### Percent read

How much of an article was read by all users on average to date.

*bug - see [1442](https://github.com/publet/publet/issues/1442)*

### Server-side requests

When a page is loaded, we record the page view on the server.  This is useful
when trying to detect bots or HTTP clients without javascript capabilities.

## Channel

### Social media referrals

How many page views were referred by social media within the last 30 days.

At this point, we're tracking:

* Facebook
* Twitter
* LinkedIn
* Google+

While it's not displayed in this graph, we record which block was the referring
one.

### Social referrals per article

As above but by article

### Social referrals per article (conversions)

How many gates were filled out and submitted as a result of a social media
referral within the last 30 days per article.

## Content

### Heatmap

This shows how much time was spent on what part of the publication.

## Reader

A list of users with a Publet account with engaged time and percent read data
attached to them.  Within the last 30 days.

## Export

### Conversions as CSV

CSV export of all information collected as part of the gate feature
