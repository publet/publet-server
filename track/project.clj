(defproject track "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :min-lein-version "2.0.0"
  :dependencies [[org.clojure/clojure "1.7.0"]
                 [publet-common "0.1.3"]
                 [cheshire "5.5.0"]
                 [compojure "1.3.4"]
                 [ring/ring-defaults "0.1.5"]
                 [ring/ring-devel "1.4.0-RC1"]
                 [com.taoensso/carmine "2.11.1"]
                 [com.taoensso/timbre  "4.0.2"]
                 [raven-clj "1.3.1"]
                 [http-kit  "2.1.18"]]
  :profiles {:uberjar {:aot :all}}
  :main ^:skip-aot track.core)
