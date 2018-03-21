(ns insights.handler
  (:require [compojure.core :refer :all]
            [compojure.route :as route]
            [clojure.java.jdbc :as jdbc]
            [cheshire.core :refer [generate-string parse-string]]
            [yesql.core :refer [defqueries]]
            [clj-time.core :as t]
            [clj-time.coerce :as c]
            [clojure.string :refer [blank?]]
            [insights.jdbc :refer [get-leads-by-time]])
  (:import org.postgresql.util.PGobject))

(def db {:classname "org.postgresql.Driver"
         :subprotocol "postgresql"
         :user (or (System/getenv "DB_USER") "postgres")
         :password (or (System/getenv "DB_PASSWORD") "postgres")
         :subname "//localhost:5432/publet"})

(defqueries "sql/basic.sql" {:connection db})
(defqueries "sql/content-metrics.sql" {:connection db})
(defqueries "sql/leads.sql" {:connection db})

;; A bit of magic for converting psql json values to json
;; Source: http://hiim.tv/clojure/2014/05/15/clojure-postgres-json/
(extend-protocol jdbc/IResultSetReadColumn
  PGobject
  (result-set-read-column [pgobj metadata idx]
    (let [type  (.getType pgobj)
          value (.getValue pgobj)]
      (case type
        "json" (parse-string value true)
        :else value))))

(defn cors-headers [req]
  ;; TODO: Don't allow every origin
  {"Access-Control-Allow-Origin" (get-in req [:headers "origin"])
   "Access-Control-Allow-Headers" "Content-Type"
   "Access-Control-Allow-Credentials" "true"
   "Access-Control-Allow-Methods" "GET,POST,OPTIONS"})

(defn mapl [k coll]
  (let [f (fn [m] [(get m k) m])]
    (apply hash-map (mapcat f coll))))

(defn new-style? [params]
  (->> params
       :data
       :new_style))

(defn get-gate-table-fn [params]
  (cond
    (new-style? params) get-lead-profiles-gate-submission
    :else               get-lead-profiles-publication-social-gate-entry))

(defn get-gate-table-name [params]
  (cond
    (new-style? params) "projects_gatesubmission"
    :else               "projects_publicationsocialgateentry"))

(defn lead-profiles [params]
  (let [gate-fn (get-gate-table-fn params)
        gate-submissions (gate-fn params)
        ids (map :anonymous_id gate-submissions)
        engaged (if (seq ids)
                  (get-engaged-data-for-lead-profiles (assoc params :ids ids))
                  [])
        read (if (seq ids)
               (get-percent-read-data-for-lead-profiles (assoc params :ids ids))
               [])
        engaged-map (mapl :anonymous_id engaged)
        read-map (mapl :anonymous_id read)]
   (map (fn [el]
          (merge el
                 (get engaged-map (:anonymous_id el))
                 (get read-map (:anonymous_id el))))
        gate-submissions)))

(defn get-time-range [start end]
  {:start (c/to-sql-time start)
   :end (c/to-sql-time end)})

(defn between-now-and-days-ago-range [days]
  (let [now (t/now)]
    (get-time-range
     (t/minus now (t/days days))
     now)))

(defn get-default-time-range []
  (between-now-and-days-ago-range 30))

(defn round [d precision]
  (when (number? d)
    (let [factor (Math/pow 10 precision)]
      (/ (Math/floor (* d factor)) factor))))

(defn round2 [n]
  (round n 2))

(defn percentage-of [total part]
  (round2 (/ part (/ total 100))))

(defn <-count
  "Extract the number from a db query that returns a count"
  [db-result]
  (->> db-result
       first
       :count))

(defn get-articles [params]
  (if (new-style? params)
    (get-new-articles params)
    (get-old-articles params)))

(defn annotate-query-with-article-data [articles coll]
  (let [article-map (apply assoc {} (mapcat (fn [a]
                                              [(:id a) a]) articles))
        f (fn [a]
            (let [article (get article-map (:id a))]
              (merge a article)))]
    (map f coll)))

(defn articles-by-avg-engaged-seconds [params articles]
  (->> (get-articles-by-avg-engaged-seconds params)
       (annotate-query-with-article-data articles)
       (sort-by :order)
       (map #(select-keys % [:id :seconds :name]))))

(defn articles-by-avg-percent-read [params articles]
  (->> (get-articles-by-avg-percent-read params)
       (annotate-query-with-article-data articles)
       (sort-by :order)
       (map #(select-keys % [:id :value :name]))))

(defn pairs-to-map [coll]
  (when (seq coll)
    (apply assoc {} (mapcat (fn [{:keys [value device]}]
                              [device value])
                            coll))))

(defn publication-dashboard [params]
  (let [articles (get-articles params)]
    {:publication_name (get-in params [:data :name])
     :avg_engaged_seconds (round2 (<-count (get-average-engaged-time params)))
     :avg_percent_read (round2 (<-count (get-average-percent-read params)))
     :readership_by_device (->> (get-readership-by-device params)
                                (pairs-to-map))
     :shares_by_channel [] ;; not collected yet
     :referrals_by_channel (get-social-referral-sources params)
     :articles_by_avg_engaged_seconds (articles-by-avg-engaged-seconds params articles)
     :articles_by_avg_percent_read (articles-by-avg-percent-read params articles)

     :actions_by_popularity (get-actions-by-popularity params)
     :leads_by_time (get-leads-by-time db (get-gate-table-name params) params)}))

(defn json-reply [req message code]
  {:status 200
   :headers (merge (cors-headers req) {"Content-Type" "application/json"})
   :body (generate-string message)})

(defn handler [req]
  (let [id (read-string (:id (:params req))) ; read-string is safe because of
                                             ; the route regex
        date-range (between-now-and-days-ago-range 1000)
        params (assoc date-range :publication id)
        publication (get-publication params {:result-set-fn first})
        params (assoc params :data publication)]
    (json-reply req
                {:dashboard (publication-dashboard params)
                 :lead_profiles (lead-profiles params)}
                200)))

(defn options [req]
  {:status 200
   :headers (cors-headers req)
   :body ""})

(defroutes app-routes
  (GET     "/api/1/publication/:id{[0-9]+}" req (handler req))
  (OPTIONS "/api/1/publication/:id{[0-9]+}" req (options req))
  (route/not-found "Not Found"))
