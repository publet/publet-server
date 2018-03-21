add-nodejs-ppa:
    pkgrepo.managed:
        - name: deb https://deb.nodesource.com/node precise main
        - dist: precise
        - file: /etc/apt/sources.list.d/nodesource.list
        - key_url: https://deb.nodesource.com/gpgkey/nodesource.gpg.key
        - refresh_db: True

nodejs:
    pkg.installed:
        - refresh: True
        - require:
            - pkgrepo: add-nodejs-ppa

bower:
    cmd.run:
        - names:
            - npm install -g bower
        - require:
            - pkg: nodejs
        - unless: which bower

uglify:
    cmd.run:
        - names:
            - npm install -g uglify-js
        - require:
            - pkg: nodejs
        - unless: which uglifyjs

gulp:
    cmd.run:
        - names:
            - npm install -g gulp
        - require:
            - pkg: nodejs
        - unless: which gulp
