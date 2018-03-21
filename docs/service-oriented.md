Service-oriented architecture
=============================

*AKA the new Publet*

```

beta.publet.com ----------->

                        /some-group/some-publications/
                        /some-group/some-other-publications/

                        nodejs, reactjs


editor.beta.publet.com ---->

                        /index.html
                        /js/app.js
                        /js/...
                        /css/...

                        publet-client, S3


api.beta.publet.com ---->

                        (url mostly invisible to user)

                        beta-2.publet.com

                        Django, PostgreSQL, REST API

track.beta.publet.com ------->

                        Kafka, JVM pipeline

```
