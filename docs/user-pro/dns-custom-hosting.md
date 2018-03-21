DNS custom hosting
==================

In order to serve a Publet-powered publication on a custom domain, the domain's
administrator must create a CNAME record pointing to `beta.publet.com.`.

```
NAME                    TYPE   VALUE
-----------------------------------------------
example.com.            CNAME  beta.publet.com.
```

If the publication was originally available at
`beta.publet.com/group/publication/`, it will now be reachable at
`example.com/group/publication/`.
