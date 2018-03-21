include:
    - nginx
    - supervisor
    - postgresql

graphite-postgres-user:
  postgres_user.present:
    - name: {{ pillar.postgresql.user }}
    - createdb: {{ pillar.postgresql.createdb }}
    - password: {{ pillar.postgresql.password }}
    - runas: postgres
    - require:
      - service: postgresql

graphite-postgres-db:
  postgres_database.present:
    - name: {{ pillar.postgresql.db }}
    - encoding: UTF8
    - lc_ctype: en_US.UTF8
    - lc_collate: en_US.UTF8
    - template: template0
    - owner: {{ pillar.postgresql.user }}
    - runas: postgres
    - require:
        - postgres_user: graphite-postgres-user

graphite-nginx-site:
    file.managed:
        - name: /etc/nginx/sites-enabled/graphite-site
        - source: salt://graphite/graphite-site.conf
        - mode: 755
        - template: jinja
        - require:
            - pkg: nginx

graphite:
    group.present:
        - name: {{ pillar.group }}
    user.present:
        - name: {{ pillar.user }}
        - groups:
            - {{ pillar.group }}
        - require:
            - group: {{ pillar.group }}

build-essential:
    pkg.installed

graphite-packages:
    pkg.installed:
        - names:
            - python-twisted
            - python-cairo
            - python-pip
            - python-django-tagging
            - postgresql-server-dev-9.3
            - python-dev
        - require:
            - pkg: build-essential

/tmp/graphite-web-0.9.10.tar.gz:
    file.managed:
        - source: salt://graphite/graphite-web-0.9.10.tar.gz

install-patched-graphite:
    cmd.run:
        - names:
          - pip install /tmp/graphite-web-0.9.10.tar.gz
          - pip install django==1.3.1
        - require:
            - file: /tmp/graphite-web-0.9.10.tar.gz
            - pkg: python-pip

graphite-pip-packages:
    pip.installed:
        - names:
            - whisper
            - carbon
            - gunicorn
            - psycopg2
        - require:
            - pkg: python-pip
            - pkg: graphite-packages
            - cmd: install-patched-graphite

{{ pillar.instdir }}:
    file.directory:
        - mode: 755

{{ pillar.webapp }}:
    file.directory:
        - mode: 755

{{ pillar.storedir }}:
    file.directory:
        - user: {{ pillar.wwwuser }}
        - group: {{ pillar.wwwuser }}
        - mode: 755

{{ pillar.storedir }}/graphite.db:
    file.managed:
        - user: {{ pillar.wwwuser }}
        - group: {{ pillar.wwwuser }}
        - mode: 755
        - require:
            - file: {{ pillar.storedir }}

install-graphite-db:
    cmd.run:
        - user: {{ pillar.wwwuser }}
        - cwd: {{ pillar.instdir }}
        - names:
            - /usr/bin/python {{ pillar.webapp }}/graphite/manage.py syncdb --noinput
        - env:
            - PYTHONPATH: {{ pillar.webapp }}:{{ pillar.instdir }}/whisper
        - require:
            - file: {{ pillar.webapp }}/graphite/local_settings.py
            - pip: graphite-pip-packages
            - postgres_database: graphite-postgres-db

{{ pillar.storedir }}/whisper:
    file.directory:
        - user: {{ pillar.user }}
        - group: {{ pillar.group }}
        - mode: 755
        - makedirs: True
        - require:
            - file: {{ pillar.storedir }}
            - group: {{ pillar.group }}
            - user: {{ pillar.user }}

{{ pillar.logdir }}:
    file.directory:
        - user: {{ pillar.wwwuser }}
        - group: {{ pillar.group }}
        - mode: 755
        - require:
            - group: {{ pillar.group }}

{{ pillar.confdir }}:
    file.directory:
        - user: root
        - group: root
        - mode: 755

{{ pillar.confdir }}/aggregation-rules.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/aggregation-rules.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/carbon.amqp.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/carbon.amqp.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/carbon.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/carbon.conf
        - template: jinja
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/dashboard.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/dashboard.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.webapp }}/graphite.wsgi:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/graphite.wsgi
        - template: jinja
        - require:
            - file: {{ pillar.webapp }}

{{ pillar.confdir }}/graphTemplates.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/graphTemplates.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/local_settings.py:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/local_settings.py
        - template: jinja
        - require:
            - file: {{ pillar.confdir }}
            - pip: graphite-pip-packages

{{ pillar.webapp }}/graphite/local_settings.py:
    file.symlink:
        - target: {{ pillar.confdir }}/local_settings.py
        - require:
            - file: {{ pillar.confdir }}/local_settings.py

{{ pillar.confdir }}/relay-rules.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/relay-rules.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/rewrite-rules.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/relay-rules.conf
        - require:
            - file: {{ pillar.confdir }}

{{ pillar.confdir }}/storage-schemas.conf:
    file.managed:
        - user: root
        - group: root
        - mode: 644
        - source: salt://graphite/storage-schemas.conf
        - require:
            - file: {{ pillar.confdir }}

/etc/supervisor/conf.d/graphite.conf:
    file.managed:
        - source: salt://graphite/graphite_supervisor.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/carbon.conf:
    file.managed:
        - source: salt://graphite/carbon_supervisor.conf
        - template: jinja
        - makedirs: True

# Riemann stuff
# -----------------------------------------------------------------------------

riemann-packages:
    pkg.installed:
        - names:
            - openjdk-7-jre

/tmp/riemann.deb:
    file.managed:
        - source: https://aphyr.com/riemann/riemann_0.2.8_all.deb
        - source_hash: sha1=2ae088d66bccc38fe990d87e4dfcc6f11bdc6b47

riemann.deb:
    cmd.run:
        - names:
            - dpkg -i /tmp/riemann.deb
        - require:
            - file: /tmp/riemann.deb

/etc/riemann/riemann.config:
    file.managed:
        - source: salt://graphite/riemann.config
        - require:
            - cmd: riemann.deb

/etc/supervisor/conf.d/riemann.conf:
    file.managed:
        - source: salt://graphite/riemann_supervisor.conf
        - makedirs: True
        - require:
            - file: /etc/riemann/riemann.config
