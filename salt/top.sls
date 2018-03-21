base:
    '*':
        - requirements.essential
        - ssh
        - users
        - publet.dirs
        - publet.security
    'precise64':
        - requirements.nodejs
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - publet.vagrant
    'vagrant-ubuntu-trusty-64':
        - requirements.nodejs
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - publet.vagrant
    'trusty64':
        - requirements.nodejs
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - publet.vagrant
    'fusion-trusty64':
        - requirements.nodejs
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - publet.vagrant
    'staging-1.publet.com':
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - requirements.nodejs
        - supervisor
        - publet.supervisor
    'staging-2.publet.com':
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - requirements.nodejs
        - supervisor
        - publet.supervisor
    'beta-1.publet.com':
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - requirements.nodejs
        - supervisor
        - publet.supervisor
    'beta-2.publet.com':
        - publet.postgresql
        - publet.requirements
        - publet.pip
        - publet.nginx
        - requirements.nodejs
        - supervisor
        - publet.supervisor
    'metrics.publet.com':
        - requirements.essential
        - ssh
        - users
        - graphite
        - publet.security
    'metrics-2.publet.com':
        - requirements.essential
        - ssh
        - users
        - graphite
        - publet.security
        - publet.postgresql
    'lb.publet.com':
        - publet.lb
    'lb-2.publet.com':
        - publet.lb
    'publications.publet.com':
        - publet.pip
        - supervisor
        - publet.supervisor-varnish
        - requirements.varnish
    'publications-staging.publet.com':
        - publet.pip
        - supervisor
        - publet.supervisor-varnish
        - requirements.varnish
