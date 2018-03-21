include:
  - postgresql

publet-postgres-user:
  postgres_user.present:
    - name: {{ pillar.postgresql.user }}
    - createdb: {{ pillar.postgresql.createdb }}
    - password: {{ pillar.postgresql.password }}
    - runas: postgres
    - require:
      - service: postgresql

publet-postgres-db:
  postgres_database.present:
    - name: {{ pillar.postgresql.db }}
    - encoding: UTF8
    - lc_ctype: en_US.UTF8
    - lc_collate: en_US.UTF8
    - template: template0
    - owner: {{ pillar.postgresql.user }}
    - runas: postgres
    - require:
        - postgres_user: publet-postgres-user

{% if pillar.env_name not in ['vagrant', 'fusion'] %}
/opt/publet/backups/backup_script:
    file.managed:
        - source: salt://publet/pg_backup_script
        - mode: 755
        - template: jinja
        - require:
            - file: /opt/publet/backups

db-backup:
    cron.present:
        - name: /opt/publet/backups/backup_script
        - minute: 0
        - require:
            - file: /opt/publet/backups/backup_script

{% endif %}

/etc/sysctl.conf:
    file.managed:
        - source: salt://publet/sysctl.conf
        - template: jinja
        - mode: 755

reload-sysctl:
    cmd.wait:
        - name: sysctl -p /etc/sysctl.conf
        - watch:
            - file: /etc/sysctl.conf
