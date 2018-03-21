vcl 4.0;

backend s3 {
  .host = "{{ pillar.publications_bucket }}.s3-website-us-east-1.amazonaws.com";
  .port = "80";
}


sub vcl_recv {
  unset req.http.cookie;
  unset req.http.cache-control;
  unset req.http.pragma;
  unset req.http.expires;
  unset req.http.etag;
  unset req.http.X-Forwarded-For;

  set req.http.host = "{{ pillar.publications_bucket }}.s3-website-us-east-1.amazonaws.com";
  set req.backend_hint = s3;
  return (hash);
}

sub vcl_backend_response {
  unset beresp.http.X-Amz-Id-2;
  unset beresp.http.X-Amz-Meta-Group;
  unset beresp.http.X-Amz-Meta-Owner;
  unset beresp.http.X-Amz-Meta-Permissions;
  unset beresp.http.X-Amz-Request-Id;
  unset beresp.http.expires;

  set beresp.ttl = 1w;
  set beresp.grace = 1h;
  set beresp.http.cache-control = "max-age=2592000";
}
