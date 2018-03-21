Services
========

* Web
* Celery
* Consumer
* Track
* Presence
* Graphs

During development, you can run all of these services with foreman.  Simply
run, `$ foreman start`.

## Web

*Python*

This is the main Django app.  It needs PostgreSQL and Redis.

## Celery

*Python*

Our worker services.  It's responsible for background tasks.  PDF exports,
theme generation, etc.  Celery is a Python based service and depends on code in
the `web` service.

## Consumer

*Python*

This service consumes tracking data, parses it and stores it in the database.
Also depends on code in the `web` service.  Also in Python.

## Track

*Clojure*

This is a service written in Clojure that tracks the movements and actions of a
user in the browser.  It submits the data to Redis.  It depends on the Redis
instance having user session data.

## Presence

*Clojure*

This service is implemented in Clojure, and removes the article lock when a user
closes the article editor.  It accepts websocket connections and when one is
broken, the lock is removed.  It also provides an HTTP interface to query the
lock status of an article.

## Graphs

*Clojure*

This is a read-only Clojure service that provides the called with analytics data.
