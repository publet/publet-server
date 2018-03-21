include:
  - nginx

publet-site:
    file.managed:
        - name: /etc/nginx/sites-available/publet-site
        {% if pillar.env_name == "vagrant" %}
        - source: salt://publet/nginx-vagrant.conf
        {% elif pillar.env_name == "fusion" %}
        - source: salt://publet/nginx-fusion.conf
        {% else %}
        - source: salt://publet/nginx.conf
        {% endif %}
        - template: jinja
        - user: deploy
        - group: deploy
        - mode: 755
        - require:
            - pkg: nginx
            - user: deploy

# Symlink and thus enable the virtual host
enable-publet-site:
    file.symlink:
        - name: /etc/nginx/sites-enabled/publet-site
        - target: /etc/nginx/sites-available/publet-site
        - force: false
        - require:
            - file: publet-site


/etc/nginx/certs/publet.com.crt:
    file.managed:
        - source: salt://publet/ssl/publet.com.crt
        - makedirs: True

/etc/nginx/certs/publet.com.key.nopass:
    file.managed:
        - source: salt://publet/ssl/publet.com.key.nopass
        - makedirs: True
