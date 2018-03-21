users:
    -
        name: honza
        groups:
            - deploy
    -
        name: nick
        groups:
            - deploy
    -
        name: david
        groups:
            - deploy
    -
        name: mj
        groups:
            - deploy
    -
        name: alex
        groups:
            - deploy
    -
        name: publetbot
        groups:
            - deploy


ssh:
    port: 41041

deploy:
    dirs:
        - /opt/publet
        - /opt/publet/apps
        - /opt/publet/apps/publet
        - /opt/publet/apps/client
        - /opt/publet/venvs
        - /opt/publet/jars
        - /opt/publet/backups
        - /opt/publet/static
        - /opt/publet/media
        - /opt/publet/vendor
        - /opt/publet/custom
        - /opt/publet/mobile/apps

domain: publications.publet.com
publications_bucket: publications-beta

env_name: varnish-beta
raven: https://eb34c96460da4709bb320d6d3fc78bad:094e66e77f394aa29464bfe1bd3c1a14@app.getsentry.com/36988