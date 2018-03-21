# Publet supervisor

/etc/supervisor/conf.d/publet.conf:
    file.managed:
        - source: salt://publet/publet.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/rq.conf:
    file.managed:
        - source: salt://publet/rq.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/build.conf:
    file.managed:
        - source: salt://publet/build.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/track.conf:
    file.managed:
        - source: salt://publet/track.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/consumer.conf:
    file.managed:
        - source: salt://publet/consumer.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/presence.conf:
    file.managed:
        - source: salt://publet/presence.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/insights.conf:
    file.managed:
        - source: salt://publet/insights.conf
        - template: jinja
        - makedirs: True

/etc/supervisor/conf.d/rqdashboard.conf:
    file.managed:
        - source: salt://publet/rqdashboard.conf
        - template: jinja
        - makedirs: True
