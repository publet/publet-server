(ns insights.core
  (:require [ring.adapter.jetty :refer [run-jetty]]
            [raven-clj.ring :refer [wrap-sentry]]
            [publet-common.middleware :as pc]
            [insights.handler :refer [app-routes]])
  (:gen-class))

(def service-name "insights")
(def dsn (System/getenv "RAVEN_DSN"))

(def app
  (-> app-routes
      ;; TODO: Caching is too aggressive, breaking CORS, figure out why
      ;; (pc/json-cache-middleware service-name 60)
      ;; (pc/request-time-middleware service-name)
      (wrap-sentry dsn)))

(defn -main [& args]
  (let [port (or (System/getenv "PORT")
                 "3030")]
    (run-jetty #'app {:port (read-string port)})))
