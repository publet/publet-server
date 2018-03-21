(function($, _) {

  var app = window.app;

  // Attention minutes

  function merge(stream1, stream2) {
    return stream1.merge(stream2);
  }

  function eventStream(eventName) {
    return $(window).asEventStream(eventName);
  }

  var DECAY = 5000; // 5s
  var EVENT_NAMES = ["focus", "click", "scroll", "mousemove", "touchstart", "touchend", "touchcancel", "touchleave", "touchmove"];

  var isFocused = eventStream("focus").map(true)
      .merge(eventStream("blur").map(false))
      .toProperty(true);

  var streams = _.map(EVENT_NAMES, eventStream);
  var activityStream = _.reduce(streams, merge);

  var recentlyActive = activityStream
      .map(true)
      .flatMapLatest(function() {
        return Bacon.once(true).merge(Bacon.once(false).delay(DECAY));
      })
      .toProperty(false);

  var isActive = recentlyActive.and(isFocused);

  var secondsActive = Bacon.mergeAll(isActive.changes(), isActive.sample(1000))
    .map(function(isActive) {
      return {
        isActive: isActive,
        timestamp: new Date().getTime()
      };
    })
    .slidingWindow(2,2)
    .filter(function(span) { return span[0].isActive; })
    .map(function(span) { return span[1].timestamp - span[0].timestamp; })
    .scan(0, function(x,y) { return x + y;})
    .map(function(x) { return x / 1000; }) // milliseconds
    .map(Math.floor);

  // Angular bits

  app.factory('Analytics', ['$http', function($http) {
    var ws = new WebSocket(window.PB.trackUrl + '/ws');
    var buffer = [];
    var ready = false;

    ws.onopen = function() {
      ready = true;

      _.each(buffer, function(el, i) {
        ws.send(el);
      });
    };

    return {
      send: function(data) {
        data = JSON.stringify(data);

        if (!ready) {
          return buffer.push(data);
        }

        return ws.send(data);
      }
    };
  }]);

  function rangeTo100(height, range) {
    var one = height / 100;

    var start = range[0];
    var end = range[1];

    var seen = [];
    var acc = start;

    while (acc < end) {
      seen.push(Math.round(acc / one));
      acc = acc + one;
    }

    return seen;

  }

  function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
  }

  function percentFromRanges(height, ranges) {
    var all = [];

    for (var i = 0; i < ranges.length; i++) {
      all = all.concat(rangeTo100(height, ranges[i]));
    }

    var len = all.filter(onlyUnique).length;

    if (len > 100) {
      return 100;
    }

    return len;
  }

  app.directive('article', function($timeout) {
    return {
      restrict: 'E',
      scope: true,
      link: function(scope, elm, attrs) {
        var $window = $(window);
        var articleId = parseInt(elm[0].id.split('-')[1], 10);
        scope.$parent.articlePercentages[articleId] = {
          height: null,
          ranges: []
        };

        var height;

        scope.getViewRange = function() {
          var visible = window.getVisibleViewport();
          var $elm = $(elm);

          height = $elm.height();

          var top = $elm.offset().top;
          var bottom = top + height;

          var topVisible = (top > visible.top) && (top < visible.bottom);
          var bottomVisible = (bottom > visible.top) && (bottom < visible.bottom);
          var middleVisible = (top < visible.top) && (bottom > visible.bottom);

          var heightVisible = 0;

          var range = null;

          if (topVisible && bottomVisible) {
            return [0, height];
          }

          if (middleVisible) {
            return [visible.top - top, visible.bottom];
          }

          if (!topVisible && !bottomVisible) {
            return [];
          }

          // top or bottom visible

          if (topVisible) {
            heightVisible = visible.bottom - top;
            return [0, heightVisible];
          }

          if (bottomVisible) {
            heightVisible = bottom - visible.top;
            return [heightVisible, height];
          }

          return [];

        };

        scope.$on('scroll', function() {
          scope.$parent.articlePercentages[articleId].height = height;
          var ranges = scope.$parent.articlePercentages[articleId].ranges;
          ranges = ranges.concat([scope.getViewRange()]);
          scope.$parent.articlePercentages[articleId].ranges = ranges;
        });

      }
    };
  });

  app.controller('PublicationController', ['$scope', 'Analytics', '$timeout', function($scope, Analytics, $timeout) {
    $scope.articlePercentages = {};

    $scope.$root.$on('identity', function() {
      window.analytics.identify(window.PB.userId, {
        agent: window.navigator.userAgent,
        languages: window.navigator.languages
      });
      Analytics.send(window._publet);
    });

    $(function() {

      var $window = $(window);
      var $body = $('body');

      var windowHeight = $window.height();
      var pageHeight = $body.height();

      var chunkCount = Math.round(pageHeight / windowHeight);
      var chunkSize = windowHeight;

      var getCurrentChunk = function(scroll) {
        return Math.round((scroll + chunkSize) / chunkSize);
      };

      var chunksSeen = [];

      var percentChunksSeen = function() {
        if (chunksSeen.length === chunkCount) {
          return 100;
        }
        return Math.round(chunksSeen.length / chunkCount * 100);
      };

      var scroll = function() {
        $scope.$broadcast('scroll');

        var curChunk = getCurrentChunk($window.scrollTop());

        if (_.indexOf(chunksSeen, curChunk) === -1) {
          chunksSeen.push(curChunk);
        }

      };

      $window.scroll(_.throttle(scroll, 300));

      var seconds = 0;
      var articleSeconds = {};
      var blockSeconds = {};

      secondsActive.onValue(function(x) {
        if (x === seconds) {
          return;
        }

        seconds++;

        var visibleArticles = window.getVisibleArticles();
        var visibleBlocks = window.getVisibleBlocks();

        visibleArticles.each(function(i, el) {
          if (articleSeconds[el.id] === undefined) {
            articleSeconds[el.id] = 1;
          } else {
            articleSeconds[el.id]++;
          }
        });

        visibleBlocks.each(function(i, el) {
          if (blockSeconds[el.id] === undefined) {
            blockSeconds[el.id] = 1;
          } else {
            blockSeconds[el.id]++;
          }
        });

      });

      window.collectAndSend = function() {
        var seen = percentChunksSeen();

        var engaged = ['engaged', {
          seconds: seconds,
          articleSeconds: articleSeconds,
          blockSeconds: blockSeconds,
          publication: window.publicationId
        }];

        var read = ['read', {
          value: seen,
          publication: window.publicationId
        }];

        var articlesRead = ['articles-read', {
          value: _.map($scope.articlePercentages, function(article, id) {
            return {
              articleId: parseInt(id, 10),
              percentRead: percentFromRanges(article.height, article.ranges)
            };
          }),
          publication: window.publicationId
        }];

        var data = window._publet.concat([engaged, read, articlesRead]);
        Analytics.send(data);
      };

      window.addEventListener('beforeunload', function(e) {
        // Try to send at the end; it's fine if it fails
        window.collectAndSend();
      });

      setInterval(function() {
        window.collectAndSend();
      }, 60 * 1000); // one minute

    });

  }]);

})(jQuery, _);
