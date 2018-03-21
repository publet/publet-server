(ns publet-common.metrics
  (:require [riemann.client :as r]
            [clojure.string :as s]))

(def host (or (System/getenv "HOST")
              "publet.example.com"))

(def env (System/getenv "ENV_NAME"))

(def client (atom nil))

(defn get-env-tag []
  (when-not (s/blank? env)
    (cond
      (.contains env "staging") "staging"
      (.contains env "beta") "beta"
      :else nil)))

(defn get-client []
  (if-let [c @client]
    c
    (do
      (let [c (r/tcp-client {:host "metrics.publet.com"})]
          (reset! client c)
          c))))

(defn send-to-riemann [metric metric-type value]
  (r/send-event (get-client) {:host host
                              :service metric
                              :tags [metric-type (get-env-tag)]
                              :metric value}))

(defn meter
  ([name]
   (meter name 1))
  ([name value]
   (send-to-riemann name "meter" value)))

(defn gauge [name value]
  (send-to-riemann (str "gauges." name) "gauge" value))

(defn histogram [name value]
  (send-to-riemann name "histogram" value))

(defn occurrence [name]
  (send-to-riemann name "occurrence" nil))

(defn timer [name value]
  (send-to-riemann name "timer" value))
