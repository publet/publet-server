New REST API
============

```
GET    /api/2/group/{id}/publications/
POST   /api/2/group/{id}/publications/

GET    /api/2/publication/{id}/
PATCH  /api/2/publication/{id}/

GET    /api/2/article/{id}/
PATCH  /api/2/article/{id}/
```

Authentication
--------------

### Logging in

Make a POST request to `/api/2/auth/` with the following payload:

```json
{
    "username": "...",
    "password": "..."
}
```

If successful, you will receive a response like this:

```json
{
    "username": "...",
    "key": "..."
}
```

You should store the username and key in order to make authenticated requests.

### Making authenticated requests


Include the `Authorization` header on all requests.  The value of the header
should be the word `Basic`, followed by a space, followed by a base64-encoded,
colon-separated, username-key pair.

```
Authorization: Basic fsdfuoi38fslkjfdsdfs
```

The username-key should simply look like:

```
username:key
```
