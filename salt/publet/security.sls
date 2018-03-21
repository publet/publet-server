# Security
#
# iptables

flush-iptables:
    cmd.run:
        - names:
            - /sbin/iptables -F
            - /sbin/iptables-restore < /etc/iptables.up.rules
        - watch:
            - file: /etc/iptables.up.rules


/etc/iptables.up.rules:
    file.managed:
        - source: salt://publet/iptables.txt
        - template: jinja


/etc/network/if-pre-up.d/iptables:
    file.managed:
        - user: root
        - mode: 644
        - contents: |
                #!/bin/sh
                sudo sh -c '/sbin/iptables-restore < /etc/iptables.save'
