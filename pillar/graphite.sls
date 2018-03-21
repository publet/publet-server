user: graphite
group: graphite
logdir: /var/log/graphite
instdir: /opt/graphite
webapp: /opt/graphite/webapp
confdir: /etc/graphite
storedir: /opt/graphite/storage
wwwuser: www-data

secret_key: "9dluhgVzt0F@ddvKyXKiZljDI&n0704sX%77MtvL"
domain: "metrics-2.publet.com"
port: 2345

postgresql:
    db: graphite
    user: graphite
    password: postgres
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

ssh:
    port: 41041

deploy:
    dirs: []

env_name: metrics
