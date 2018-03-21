(ns publet-common.middleware
  (:require [publet-common.metrics :refer [timer meter]]
            [taoensso.carmine :as car :refer (wcar)]))

(defn minutes [n] (* n 60))

;; TODO: Add support for If-Modified-Since

(defmacro wcar* [& body]
  `(car/wcar
    {:spec
     {:host "localhost"
      :db 0}}
    ~@body))

(defn make-redis-key [url]
  url)

(defn get-cached-data [url]
  (wcar* (car/get (make-redis-key url))))

(defn cache-data
  "Expires in 60mins"
  [url data expiry]
  (wcar*
   (car/set
    (make-redis-key url)
    data
    "EX"
    (minutes expiry))))

;; -----------------------------------------------------------------------------
;; Public API

(defn json-cache-middleware [handler service-name expiry]
  (fn [request]
    (let [url       (:uri request)
          cache-key (str service-name ":" url)
          cached    (get-cached-data cache-key)]
      (if cached
        (do
          (meter (str service-name ".cache-hit"))
          {:status 200
           :headers {"Content-Type" "application/json"}
           :body cached})
        (let [response (handler request)
              data     (:body response)]
          (meter (str service-name ".cache-miss"))
          (cache-data cache-key data expiry)
          response)))))

(defn request-time-middleware [handler service-name]
  (fn [request]
    (let [start (System/nanoTime)
          response (handler request)
          end (System/nanoTime)
          elapsed (/ (double (- end start)) 1000000)]
      (timer (str service-name ".response-time") elapsed)
      response)))
