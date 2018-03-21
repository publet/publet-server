envs:
    - staging
    - beta

users:
    -
        name: honza
        groups:
            - deploy
    -
        name: nick
        groups:
            - deploy
    -
        name: david
        groups:
            - deploy
    -
        name: trusktr
        groups:
            - deploy

deploy:
  dirs: []

ssh:
    port: 41041

env_name: lb
