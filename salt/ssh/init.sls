openssh-server:
    pkg:
        - installed

ssh:
    service:
        - running
        - watch:
            - file: /etc/ssh/sshd_config
            - file: /etc/network/if-pre-up.d/iptables
        - require:
            - pkg: openssh-server

/etc/ssh/sshd_config:
    file.managed:
        - source: salt://ssh/sshd_config
        - template: jinja
        - mode: 644
        - user: root
