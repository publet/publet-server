include:
    - packages

/tmp/elasticsearch-1.5.2.deb:
    file.managed:
        - source: https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.5.2.deb
        - source_hash: sha1=2595e14de7133fa23db90f83c83c84c0ea08468a

elasticsearch-1.5.2.deb:
    cmd.run:
        - names:
            - dpkg -i /tmp/elasticsearch-1.5.2.deb
        - require:
            - file: /tmp/elasticsearch-1.5.2.deb
            - pkg: publet-packages

elasticsearch:
    service:
        - running
        - enable: True
        - require:
            - cmd: elasticsearch-1.5.2.deb

# These are taken from the wkhtmltopdf build script
wkhtmltopdf-deps:
    pkg.installed:
        - names:
            - fontconfig
            - libfontconfig1
            - libfreetype6
            - libpng12-0
            - zlib1g
            - libjpeg-turbo8
            - libssl1.0.0
            - libx11-6
            - libxext6
            - libxrender1
            - xfonts-base
            - xfonts-75dpi
            - libstdc++6
            - libc6


/tmp/wkhtmltopdf.deb:
    file.managed:
        - source: http://downloads.sourceforge.net/project/wkhtmltopdf/0.12.2.1/wkhtmltox-0.12.2.1_linux-trusty-amd64.deb
        - source_hash: sha1=5c509de79121e96908794ebcb9d16647a9385e1d

wkhtmltopdf.deb:
    cmd.run:
        - names:
            - dpkg -i /tmp/wkhtmltopdf.deb
        - require:
            - file: /tmp/wkhtmltopdf.deb
            - pkg: nodejs
            - pkg: nginx
            - pkg: python-pip
            - pkg: publet-packages
            - pkg: wkhtmltopdf-deps

redis-tar:
    file.managed:
        - name: /tmp/redis-3.0.4.tar.gz
        - source: http://download.redis.io/releases/redis-3.0.4.tar.gz
        - source_hash: sha1=cccc58b2b8643930840870f17280fcae57ed7675

extract-redis:
    cmd.run:
        - cwd: /tmp
        - names:
            - tar xvf redis-3.0.4.tar.gz
        - require:
            - file: redis-tar
        - unless: which redis-server

install-redis:
    cmd.run:
        - cwd: /tmp/redis-3.0.4
        - names:
            - make install
        - require:
            - cmd: extract-redis
            - pkg: essential-packages
        - unless: which redis-server

redis-init:
    file.managed:
        - name: /etc/init.d/redis
        - source: salt://publet/redis-init
        - mode: 744
        - require:
            - cmd: install-redis

redis-conf:
    file.managed:
        - name: /etc/redis/redis.conf
        - source: salt://publet/redis.conf
        - makedirs: True

redis:
    service.running:
        - name: redis
        - require:
            - file: redis-init
            - file: redis-conf

# This used to be rubygems.  However, rubygems is now part of ruby.
ruby:
    pkg.installed

sass:
    gem.installed:
        - version: 3.4.5
        - require:
            - pkg: ruby

/etc/rc.local:
    file.managed:
        - source: salt://publet/rc.local
        - template: jinja
        - mode: 755


/tmp/telegraf.deb:
    file.managed:
        - source: https://s3.amazonaws.com/get.influxdb.org/telegraf/telegraf_0.2.0_amd64.deb
        - source_hash: sha1=9af02720eeded3db4848b00e4c0aa28ef9d254df

telegraf.deb:
    cmd.run:
        - names:
            - dpkg -i /tmp/telegraf.deb
        - require:
            - file: /tmp/telegraf.deb

/etc/opt/telegraf/telegraf.conf:
    file.managed:
        - source: salt://publet/telegraf.conf
        - template: jinja
        - mode: 755
        - require:
            - cmd: telegraf.deb

telegraf:
    service:
        - running
        - enable:  True
        - require:
            - file: /etc/opt/telegraf/telegraf.conf