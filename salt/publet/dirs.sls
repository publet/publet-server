{% for dir in pillar.deploy.dirs %}
{{ dir }}:
    file.directory:
        - user: deploy
        - group: deploy
        - mode: 775
        - makedirs: True
        - require:
            - group: deploy
            - user: deploy
{% endfor %}
