(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  var VIMEO_REGEX = /https?:\/\/([^\/]+\.)?vimeo.com\/(channels\/[\w]+[#|\/])?(\d+)/;
  var YOUTUBE_URL_PATTERNS = [
    /youtube.com\/.*?v[\/=]([\w-]+)/,
    /youtu.be\/([w-]+)/
  ];

  function extractYouTubeId(url) {
    var match;

    for (var i = 0; i < YOUTUBE_URL_PATTERNS.length; i++) {
      match = url.match(YOUTUBE_URL_PATTERNS[i]);
      if (match) {
        return match[1];
      }
    }
  }

  function extractVimeoId(url) {
    var match = url.match(VIMEO_REGEX);

    if (match) {
      return match[3];
    }
  }

  function getVideoType(url) {
    if (containsAny(url, ['youtube.com', 'youtu.be'])) {
      return 'youtube';
    }

    if (contains(url, 'vimeo')) {
      return 'vimeo';
    }

    throw 'contains nothing';
  }

  function videoIdFromUrl(url) {
    if (getVideoType(url) === 'youtube') {
      return extractYouTubeId(url);
    }

    if (getVideoType(url) === 'vimeo') {
      return extractVimeoId(url);
    }

    return null;

  }

  app.getVideoType = getVideoType;

  // TODO: Resize player on position change
  app.directive('youtubeVideo', ['$window', '$parse', '$timeout', function ($window, $parse, $timeout) {
    return {
      //scope: true,
      link: function (scope, elem, attrs) {
        var countVideosLoaded = 0;
        var player;

        $timeout(function() {
          var blockOpts = $parse(attrs.youtubeVideo)(scope);

          var vParts = elem.attr('id').split('-');
          var videoPk = vParts[1];

          scope.$on('video-url-changed', function() {
            var videoId = videoIdFromUrl(scope.block.video_url);
            scope.videoId = videoId;
            player.clearVideo();
            player.destroy();
            player = null;
            addPlayer();
          });

          scope.getVideoId = function() {
            if (scope.videoId) {
              return scope.videoId;
            }

            if (blockOpts && blockOpts.videoId) {
              scope.videoId = blockOpts.videoId;
              return scope.videoId;
            }

            if (scope.block && scope.block.video_id) {
              scope.videoId = scope.block.video_id;
              return scope.videoId;
            }

            scope.videoId = vParts.splice(2, 100).join('-');
            return scope.videoId;

          };

          scope.previewActive = true;

          function addPlayer() {
            if (!YT.Player) {
              return $timeout(addPlayer, 500);
            }

            if (player) {
              return;
            }

            var width = 700;
            var alignment = null;

            if (scope.block) {
              alignment = scope.block.alignment;
            } else {
              alignment = blockOpts.alignment;
            }

            if (alignment) {

              // Breaking
              if (alignment == '2') {
                width = 960;
                // (960 - 700) / 2 = 130
                scope.videoStyle = 'margin-left: -130px';
              }

              // Full
              if (alignment == '1') {
                width = window.innerWidth;
                scope.videoStyle = 'margin-left: -' + ((width - 700) / 2) + 'px';
              }

              // Breaking left and breaking right
              if (alignment == '3' || alignment == '4') {
                width = 460;
              }

              // Margin left and margin right
              if (alignment == '5' || alignment == '6') {
                width = 220;
              }

            }

            player = new YT.Player('video-' + videoPk, {
              videoId: scope.getVideoId(),
              width: width,
              height: width / 1.77777,
              events: {
                onReady: function() {
                  countVideosLoaded++;
                  if (countVideosLoaded == 1) { // only emit on the first load.
                    scope.$root.$broadcast('blockLoaded');
                  }
                }
              }
            });

          }

          addPlayer();

          scope.play = function() {
            if (player && player.playVideo) {
              scope.previewActive = false;
              player.playVideo();
            }
          };

        });
      }
    };
  }]);

  // This is such a hack, I can't even believe I did that.  It's so convoluted
  // and 'complected' --- ugh.  I apologize that I couldn't make it any better.
  app.directive('vimeoVideo', ['$window', '$timeout', '$parse', function ($window, $timeout, $parse) {
    return {
      //scope: true,
      link: function (scope, elem, attrs) {
        var countVideosLoaded = 0;
        var parsed = $parse(attrs.vimeoVideo)(scope) || {};

        scope.videoId = parsed.id;
        scope.blockId = attrs.id;
        scope.ratio = parsed.ratio;
        scope.alignment = parsed.alignment;
        scope.previewActive = true;

        scope.getVideoHeight = function() {
          if (!scope.ratio) {
            return;
          }
          return scope.getVideoWidth() / scope.ratio;
        };

        scope.getVideoWidth = function() {
          var a;

          scope.videoStyle = '';

          if (scope.alignment === undefined) {
            a = scope.block.alignment;
          } else {
            if (scope.alignment === '') {
              a = '0';
            } else {
              a = scope.alignment;
            }
          }

          if (a === '1') {
            scope.videoStyle = 'margin-left: -' + ((window.innerWidth - 700) / 2) + 'px';
            return window.innerWidth;
          }

          if (a === '2') {
            return 960;
          }

          if (a === '3' || a === '4') {
            return 460;
          }

          if (a === '5' || a === '6') {
            return 220;
          }

          return 700;
        };

        scope.getBlockId = function() {
          if (scope.$parent && scope.$parent.block) {
            return scope.$parent.block.id;
          } else {
            return attrs.id;
          }
        };

        scope.getIframeUrl = function() {
          if (!scope.videoId) {
            return;
          }
          return "https://player.vimeo.com/video/" + scope.videoId +
            "?api=1&player_id=" + scope.getBlockId();
        };

        var init = function() {
          if (scope.$parent.findVideoTypeFromBlock && scope.$parent.findVideoTypeFromBlock() !== 'vimeo') {
            return;
          }

          if (!scope.videoId) {
            var videoId = extractVimeoId(scope.$parent.block.video_url);

            if (!videoId) {
              $timeout(init, 200);
              return;
            } else {
              scope.videoId = videoId;
            }
          }

          VIMEO.register(scope.getBlockId(), $(elem).find('iframe'), function() {
            // on ready...
            if (scope.ratio) {
              scope.$apply();
            } else {
              VIMEO.getVideoSize(scope.getBlockId(), function(data) {
                var ratio = data.width / data.height;
                scope.ratio = Math.round(ratio * 100) / 100;
                scope.$apply();
              });
            }
            countVideosLoaded++;
            if (countVideosLoaded == 1) { // only emit on the first load
              scope.$root.$broadcast('blockLoaded');
            }
          });

        };

        $timeout(function() {
          init();
        });

        scope.$on('video-url-changed', function() {
          scope.videoId = null;
          init();
        });

        scope.play = function() {
          scope.previewActive = false;
          VIMEO.play(scope.getBlockId());
        };

      }
    };
  }]);

})(window);
