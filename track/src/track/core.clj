(ns track.core
  (:require [publet-common.metrics :refer [meter]]
            [cheshire.core :refer [generate-string parse-string]]
            [compojure.core :refer :all]
            [compojure.route :as route]
            [org.httpkit.server :refer :all]
            [compojure.handler :refer [site]]
            [ring.middleware.reload :as reload]
            [raven-clj.ring :refer [wrap-sentry]]
            [taoensso.timbre :refer [info error]]
            [taoensso.carmine :as car :refer (wcar)])
  (:gen-class))

(def clients "track:clients")
(def queue "track:queue")
(def dsn (System/getenv "RAVEN_DSN"))

(defmacro wcar* [& body]
  `(car/wcar
     {:spec
      {:host (or (System/getenv "HOST")
                 "publet.example.com")
       :db 0}}
     ~@body))

(defn uuid []
  (str (java.util.UUID/randomUUID)))

(defn get-client-list-key [id]
  (str "track:clients:" id))

(defn push-to-client-list [key data]
  (wcar*
    (car/rpush key data)))

(defn push [key data ip]
  (let [parsed-data (parse-string data)
        data {:data parsed-data
              :ip ip}]
    (push-to-client-list key (generate-string data))))

(defn close-client-session [key]
  (wcar*
    (car/rpoplpush key queue)
    (car/del key)))

(defn ws [req]
  (let [id        (uuid)
        redis-key (get-client-list-key id)
        ip        (:remote-addr req)]

    (info "connection opened")
    (meter "track.connection.opened")

    (with-channel req channel
      (on-close channel (fn [status]
                          (close-client-session redis-key)
                          (info "connection closed")
                          (meter "track.connection.closed")))
      (on-receive channel
                  (fn [data]
                    (push redis-key data ip)
                    (info "data sent to redis"))))))

(defroutes app-routes
  (GET "/ws" req (ws req))
  (GET "/error" req (fn [req]
                      (throw (Exception. "Test"))))
  (route/not-found "Not Found"))

(def app
  (-> app-routes
      (wrap-sentry dsn)
      ring.middleware.keyword-params/wrap-keyword-params
      ring.middleware.params/wrap-params))

(defn in-dev?
  "TODO: Use environ for configuration"
  [& args]
  (some? (System/getenv "DEBUG")))

(defn -main [& args] ;; entry point, lein run will pick up and start from here
  (let [handler (if (in-dev?)
                  (reload/wrap-reload (site #'app)) ;; only reload when dev
                  (site app))
        port    (or (System/getenv "PORT")
                    "3000")]
    (run-server handler {:port (read-string port)})
    (info "server running" port)))
