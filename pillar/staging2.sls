python:
    virtualenv: /opt/publet/venvs/publet

django:
    path: /opt/publet/apps/publet
    settings: publet.settings_staging
    user: deploy
    group: deploy

postgresql:
    db: publet
    user: publet
    password: ahP5A7CkOcN7Mgo8lbRtPto4F6xnsihHJh
    createdb: True
    shared_buffers: 512 # 25% of RAM
    shmmax: 1073741824 # 1024 * 1024 * 1024 # shared_buffers * 2
    effective_cache_size: 1024 # 50% of RAM
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
        name: ci
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

domain: staging-2.publet.com
short_host: staging.pblt.co
publications_bucket: publications-staging
publications_url_host: publications-staging.publet.com

env_name: staging
protected_path: /opt/publet/apps/publet/publet/renders/
custom_publication_path: /opt/publet/custom/
raven: https://ed0de1c1f0db44fe88ae34ab9beb1731:5d8eef6eabcd41dea69c9deaac9e13ef@app.getsentry.com/36987
