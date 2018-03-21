add-varnish-ppa:
    pkgrepo.managed:
        - name: deb https://repo.varnish-cache.org/ubuntu/ trusty varnish-4.0
        - dist: precise
        - file: /etc/apt/sources.list.d/varnish.list
        - key_url: https://repo.varnish-cache.org/GPG-key.txt
        - refresh_db: True

varnish:
    pkg.installed:
        - refresh: True
        - require:
            - pkgrepo: add-varnish-ppa
    service:
        - running
        - enable: True
        - watch:
            - file: /etc/default/varnish
            - file: /etc/varnish/default.vcl

/etc/varnish/default.vcl:
    file.managed:
        - source: salt://publet/varnish.vcl
        - user: root
        - mode: 400
        - template: jinja
        - require:
            - pkg: varnish

/etc/default/varnish:
    file.managed:
        - source: salt://publet/varnish-default
        - user: root
        - mode: 400
        - template: jinja
        - require:
            - pkg: varnish