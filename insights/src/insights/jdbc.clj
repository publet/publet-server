(ns insights.jdbc
  (:require [clojure.java.jdbc :as j]))

(defn leads-by-time-query [table]
  (str "with filled_dates as (
      select date_trunc('day', day) as day, 0 as blank_count
          from generate_series(?,current_date::date, '1 day') as day
  ),
  for_pub as (
      select * from " table " where publication_id = ?
  ),
  daily_counts as (
      select date_trunc('day', created) as day, count(*) as value
          from for_pub
          group by date_trunc('day', created)
  )
  select filled_dates.day,coalesce(daily_counts.value, filled_dates.blank_count) as count
      from filled_dates
      join daily_counts on daily_counts.day = filled_dates.day
      order by filled_dates.day;"))

(defn get-leads-by-time
  "Return a list of objects; there is an object for each day of the
  publication's existence.  Includes lead count for each day."
  [spec table {:keys [publication data]}]
  (j/query spec [(leads-by-time-query table) (:created data) publication]))
