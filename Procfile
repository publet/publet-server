web: /opt/publet/venvs/publet/bin/python manage.py runserver --settings=publet.settings_vagrant
celery: /opt/publet/venvs/publet/bin/celery -A publet worker --autoreload --loglevel=info
consumer: /opt/publet/venvs/publet/bin/python manage.py consumer --settings=publet.settings_vagrant
track: java -Xmx256m -jar track/target/track-0.1.0-SNAPSHOT-standalone.jar
