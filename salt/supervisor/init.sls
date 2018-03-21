# Supervisor

supervisor:
    pip.installed:
        - require:
            - pkg: python-pip

/etc/supervisord.conf:
    file.managed:
        - source: salt://supervisor/supervisord.conf

/etc/init.d/supervisord:
    file.managed:
        - source: salt://supervisor/supervisord.init.sh
        - user: root
        - mode: 755

/var/log/supervisor:
    file.directory

/etc/supervisor/conf.d:
    file.directory:
        - makedirs: True

supervisord:
    service.running:
        - require:
            - file: /etc/init.d/supervisord
            - file: /var/log/supervisor
        - watch:
            - file: /etc/supervisord.conf
            - file: /etc/supervisor/conf.d/*
