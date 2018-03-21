-- name: get-lead-profiles-gate-submission
select anonymous_id, created, data from projects_gatesubmission
    where
        publication_id = :publication
        and anonymous_id != '';

-- name: get-lead-profiles-publication-social-gate-entry
select anonymous_id, created from projects_publicationsocialgateentry
    where
        publication_id = :publication
        and anonymous_id != '';

-- name: get-engaged-data-for-lead-profiles
select anonymous_id, sum(seconds) as engaged_seconds from analytics_event
    where
        publication_id = :publication
        and anonymous_id in (:ids)
    group by anonymous_id;

-- name: get-percent-read-data-for-lead-profiles
select anonymous_id, max(percent_read) as percent_read from analytics_event
    where
        publication_id = :publication
        and anonymous_id in (:ids)
    group by anonymous_id;
