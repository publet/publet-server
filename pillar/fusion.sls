python:
    virtualenv: /opt/publet/venvs/publet

django:
    path: /vagrant
    settings: publet.settings_fusion
    user: vagrant
    group: vagrant

postgresql:
    db: publet
    user: postgres
    password: postgres
    createdb: True
    shared_buffers: 64 # 25% of RAM (128mb)
    shmmax: 134217728 # 128 * 1024 * 1024 # shared_buffers * 2
    effective_cache_size: 128 # 50% of RAM (128mb)
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

ssh:
    port: 22

deploy:
    dirs:
        - /opt/publet
        - /opt/publet/apps
        - /opt/publet/apps/publet
        - /opt/publet/venvs
        - /opt/publet/backups
        - /opt/publet/static
        - /opt/publet/media
        - /opt/publet/vendor
        - /opt/publet/custom
        - /opt/publet/mobile/apps

domain: publet.example.com
short_host: pblt.example.com

env_name: fusion
protected_path: /vagrant/publet/renders/
custom_publication_path: /opt/publet/custom/
