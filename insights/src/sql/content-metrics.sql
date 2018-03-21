-- name: get-unique-visitors
with distinct_entries as (
    select distinct on (anonymous_id) anonymous_id
    from analytics_event
    where
        publication_id = :publication
        and type = 'page'
        and created > :start
        and created < :end
)
select count(*) from distinct_entries;

-- name: get-article-unique-visitors
with distinct_entries as (
    select distinct on (anonymous_id) anonymous_id
    from analytics_event
    where
        article_id = :article
        and type = 'page'
        and created > :start
        and created < :end
)
select count(*) from distinct_entries;

-- name: get-average-engaged-time
select round(avg(seconds)) as count from analytics_event
    where
        publication_id = :publication
        and type = 'engaged_publication'
        and created > :start
        and created < :end

-- name: get-article-average-engaged-time
select round(avg(seconds)) as count from analytics_event
    where
        article_id = :article
        and type = 'engaged_article'
        and created > :start
        and created < :end

-- name: get-average-percent-read
select round(avg(percent_read)::numeric,2) as count from analytics_event
    where
        publication_id = :publication
        and type = 'read_publication'
        and created > :start
        and created < :end

-- name: get-article-average-percent-read
select round(avg(percent_read)::numeric,2) as count from analytics_event
    where
        article_id = :article
        and type = 'read_article'
        and created > :start
        and created < :end

-- name: get-social-referral-sources
select social_referrer as name, count(*) as value from analytics_event
    where
        social_referrer != ''
        and social_referrer is not null
        and publication_id = :publication
        and type = 'page'
        and created > :start
        and created < :end
    group by social_referrer order by value desc;

-- name: get-article-social-referral-sources
select social_referrer as name, count(*) as value from analytics_event
    where
        social_referrer != ''
        and social_referrer is not null
        and article_id = :article
        and type = 'page'
        and created > :start
        and created < :end
    group by social_referrer order by value desc;

-- name: get-revisit-count
with user_visits as (
    select anonymous_id, count(*) from analytics_event
        where
            publication_id = :publication
            and type = 'page'
            and created > :start
            and created < :end
        group by anonymous_id
)
select count(*) from user_visits
    where
        count > 1;

-- name: get-article-revisit-count
with user_visits as (
    select anonymous_id, count(*) from analytics_event
        where
            article_id = :article
            and type = 'page'
            and created > :start
            and created < :end
        group by anonymous_id
)
select count(*) from user_visits
    where
        count > 1;

-- name: get-conversion-count
select count(*) from projects_gatesubmission
    where
        publication_id = :publication
        and created > :start
        and created < :end

-- name: get-old-articles
select * from projects_article
    where
        publication_id = :publication
    order by "order"

-- name: get-new-articles
select * from projects_newarticle
    where
        publication_id = :publication
    order by "order"

-- name: get-articles-by-avg-engaged-seconds
select article_id as id,round(avg(seconds)) as seconds from analytics_event
    where
        publication_id = :publication
        and type = 'engaged_article'
    group by article_id

-- name: get-articles-by-avg-percent-read
select article_id as id,round(avg(percent_read)::numeric,2) as value from analytics_event
    where
        publication_id = :publication
        and type = 'read_article'
    group by article_id

-- name: get-readership-by-device
select device,count(*) as value from analytics_event
    where
        publication_id = :publication
        and device is not null
        and type = 'page'
     group by device

-- name: get-actions-by-popularity
select action_name as name, count(*) as value from analytics_event
    where
        publication_id = :publication
        and action_type != ''
    group by action_name;
