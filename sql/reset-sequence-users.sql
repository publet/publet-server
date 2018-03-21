BEGIN;
SELECT setval(pg_get_serial_sequence('"users_publetuser"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "users_publetuser";
SELECT setval(pg_get_serial_sequence('"users_publetapikey"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "users_publetapikey";
COMMIT;
