(defproject insights "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :min-lein-version "2.0.0"
  :dependencies [[org.clojure/clojure "1.6.0"]
                 [publet-common "0.1.4"]
                 [compojure "1.4.0"]
                 [raven-clj "1.3.1"]
                 [yesql "0.5.0-rc3"]
                 [org.postgresql/postgresql "9.3-1102-jdbc41"]
                 [ring/ring-jetty-adapter "1.4.0"]
                 [ring/ring-defaults "0.1.5"]
                 [cheshire "5.5.0"]
                 [com.taoensso/carmine "2.11.1"]
                 [clj-time "0.11.0"]]
  :plugins [[lein-ring "0.8.13"]]
  :main ^:skip-aot insights.core
  :ring {:handler insights.handler/app-routes}
  :profiles {:dev {:dependencies [[javax.servlet/servlet-api "2.5"]
                                  [ring-mock "0.1.5"]]}
             :uberjar {:aot :all}})
