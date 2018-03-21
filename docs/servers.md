Server layout
=============

This is all on AWS EC2.

```
*.publet.com
    |
    |
    \-------> lb.publet.com --------> staging-2.publet.com
               nginx                   nginx, gunicorn
               SSL                      no SSL
               |
               |
               \-----> beta-2.publet.com
                        nginx, gunicorn
                         no SSL
```

Provisioning a new server environment
-------------------------------------

Here, an environment is understood to mean something like `beta` or `staging`.

1.  Create a new VM
2.  Create an A record for the VM's IP address
3.  Copy the `staging` env in `fabfile.py` and rename to match the new env
4.  Update the contents of the function with the appropriate values
5.  Add an env file in `pillar/`
6.  Plug the new env into `pillar/top.sls`
7.  Add the new env into `salt/top.sls`
8.  `$ fab <your new env> prepare`
