(ns presence.core
  (:require [publet-common.metrics :refer [meter]]
            [compojure.core :refer :all]
            [compojure.route :as route]
            [compojure.handler :refer [site]]
            [org.httpkit.server :refer :all]
            [ring.middleware.reload :as reload]
            [raven-clj.ring :refer [wrap-sentry]]
            [cheshire.core :refer [parse-string generate-string]]
            [taoensso.timbre :refer [info]]
            [taoensso.carmine :as car :refer (wcar)])
  (:gen-class))

(def dsn (System/getenv "RAVEN_DSN"))
(def redis-key-prefix ":0")

(defmacro wcar* [& body]
  `(car/wcar
    {:spec
     {:host (or (System/getenv "HOST")
                "publet.example.com")
      :db 0}}
    ~@body))

;; Helpers

(defn get-session-key [publet-id]
  (str redis-key-prefix ":django.contrib.sessions.cache" publet-id))

(defn get-lock-key [article-id]
  (str redis-key-prefix ":article:edited:" article-id))

(defn get-user-id [publet-id]
  (let [key (get-session-key publet-id)]
    (when-let [session (wcar* (car/get key))]
      (get (parse-string session) "_auth_user_id"))))

(defn release-lock [user-id article-id]
  (let [key (get-lock-key article-id)
        lock-val (wcar* (car/get key))]
    (when (= lock-val user-id)
      (wcar*
       (car/del key)))))

;; Handlers

(defn ws [req]
  (let [publet-id (:value (get (:cookies req) "publetid"))
        article-id (read-string (:id (:params req)))
        user-id (get-user-id publet-id)]

    (meter "presence.connection.open")
    (info "connection opened")

    (with-channel req channel
      (on-close channel (fn [_]
                          (release-lock user-id article-id)
                          (meter "presence.connection.close")
                          (info "connection closed"))))))

(defn lock-handler [req]
  (let [article-id (read-string (:id (:params req)))
        key (get-lock-key article-id)
        lock-value (wcar* (car/get key))]
    {:status 200
     :body (generate-string {:user lock-value})
     :headers {"Content-Type" "application/json"}}))

;; App

(defroutes app-routes
  (GET "/ws/:id{[0-9]+}"   req (ws req))
  (GET "/lock/:id{[0-9]+}" req (lock-handler req))
  (route/not-found "Not Found"))

(def app
  (-> app-routes
      (wrap-sentry dsn)
      ring.middleware.keyword-params/wrap-keyword-params
      ring.middleware.params/wrap-params))

(defn in-dev?
  [& args]
  (some? (System/getenv "DEBUG")))

(defn -main [& args]
  (let [handler (if (in-dev?)
                  (reload/wrap-reload (site #'app))
                  (site app))
        port    (or (System/getenv "PORT")
                    "2000")]
    (run-server handler {:port (read-string port)})
    (info "server running" port)))
