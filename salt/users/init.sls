deploy:
    group.present:
        - name: deploy
        - require:
            - user: deploy
    user.present:
        - name: deploy
    file.managed:
        - name: /home/deploy/.ssh/id_rsa
        - user: deploy
        - mode: 700
        - source: salt://users/deploy
        - makedirs: True
        - require:
            - user: deploy

admin:
    group.present:
        - name: admin

{% for user in pillar['users'] %}
{{ user.name }}:
    user.present:
        - name: {{ user.name }}
        - home: /home/{{ user.name }}
        - shell: /bin/bash
        - groups: {{ user.groups }}
        - require:
            - group: deploy
            - group: admin
    ssh_auth.present:
        - user: {{ user.name }}
        - source: salt://users/{{ user.name }}.pub
        - makedirs: True
        - require:
            - user: {{ user.name }}
    {% if pillar.env_name != "lb" %}
    file.managed:
        - name: /home/{{ user.name }}/.bashrc
        - user: {{ user.name }}
        - source: salt://users/staging-bashrc
        - makedirs: True
        - template: jinja
        - require:
            - user: {{ user.name }}
    {% endif %}
{% endfor %}

{% if pillar.env_name in ["vagrant", "fusion"] %}
bashrc:
    file.managed:
        - name: /home/vagrant/.bashrc
        - source: salt://users/vagrant-bashrc
        - template: jinja
        - user: vagrant
{% endif %}

/etc/sudoers:
    file.managed:
        - source: salt://users/sudoers
        - mode: 440
