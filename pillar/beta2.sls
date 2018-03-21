python:
    virtualenv: /opt/publet/venvs/publet

django:
    path: /opt/publet/apps/publet
    settings: publet.settings_beta
    user: deploy
    group: deploy

postgresql:
    db: publet
    user: publet
    password: ahP5A7CkOcN7Mgo8lbRtPto4F6xnsihHJh
    createdb: True
    shared_buffers: 2048 # 25% of RAM
    shmmax: 4294967296 # 4096 * 1024 * 1024 # shared_buffers * 2
    effective_cache_size: 4096 # 50% of RAM
    work_mem: 5

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
        - /opt/publet/bin
        - /opt/publet/backups
        - /opt/publet/static
        - /opt/publet/media
        - /opt/publet/vendor
        - /opt/publet/custom
        - /opt/publet/mobile/apps

domain: beta-2.publet.com
short_host: pblt.co
publications_bucket: publications-beta
publications_url_host: publications.publet.com

env_name: beta
protected_path: /opt/publet/apps/publet/publet/renders/
custom_publication_path: /opt/publet/custom/

raven: https://eb34c96460da4709bb320d6d3fc78bad:094e66e77f394aa29464bfe1bd3c1a14@app.getsentry.com/36988