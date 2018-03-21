include:
    - nginx

{% for env in pillar.envs %}
/etc/nginx/sites-available/{{ env }}:
    file.managed:
        - source: salt://publet/lb/{{ env }}.conf
        - makedirs: True
        - user: deploy
        - group: deploy
        - mode: 755
        - require:
            - pkg: nginx
            - user: deploy

/etc/nginx/sites-available/maintenance-{{ env }}:
    file.managed:
        - source: salt://publet/lb/maintenance.conf
        - template: jinja
        - makedirs: True
        - user: deploy
        - group: deploy
        - mode: 755
        - context:
            domain: {{ env }}.publet.com
        - require:
            - pkg: nginx
            - user: deploy

/etc/nginx/sites-enabled/{{ env }}:
    file.symlink:
        - target: /etc/nginx/sites-available/{{ env }}
        - require:
            - file: /etc/nginx/sites-available/{{ env }}
{% endfor %}

/etc/nginx/certs/publet.com.crt:
    file.managed:
        - source: salt://publet/ssl/publet.com.crt
        - makedirs: True

/etc/nginx/certs/publet.com.key.nopass:
    file.managed:
        - source: salt://publet/ssl/publet.com.key.nopass
        - makedirs: True

/opt/maintenance.html:
    file.managed:
        - source: salt://publet/lb/maintenance.html
        - makedirs: True
        - user: deploy
        - group: deploy
        - mode: 755
        - require:
            - pkg: nginx
            - user: deploy

/etc/nginx/sites-enabled/analytics.conf:
    file.managed:
        - source: salt://publet/lb/analytics.conf
        - makedirs: True
        - user: deploy
        - group: deploy
        - mode: 755
        - require:
            - pkg: nginx
            - user: deploy
