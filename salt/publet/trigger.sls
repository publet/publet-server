trigger-tar:
    file.managed:
        - name: /tmp/TriggerToolkit.tar.gz
        - source: https://toolkit-installer.s3.amazonaws.com/3.3.64/TriggerToolkit.tar.gz
        - source_hash: sha1=556e0256f179390f617b587f6a25ba836bbc2a34

extract-trigger:
    cmd.run:
        - cwd: /tmp
        - names:
            - tar xvf TriggerToolkit.tar.gz
        - require:
            - file: trigger-tar

install-trigger:
    cmd.run:
        - names:
            - mv /tmp/TriggerToolkit /opt/publet/vendor/TriggerToolkit
        - require:
            - cmd: extract-trigger
            - file.directory: /opt/publet/vendor
