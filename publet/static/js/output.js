(function($) {

  // Core app.
  var app = angular.module('Publet', []);

  // Use non-Django-style interpolation.
  app.config(['$interpolateProvider', '$locationProvider', function($interpolateProvider, $locationProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
  }]);

  var numLoaded = 0;
  var iframeMessageEvent = null;
  var gateFilled = false;
  var interval = null;
  var heights = [];

  function decode(integer) {
    var BASE = 62;
    var UPPERCASE_OFFSET = 55;
    var LOWERCASE_OFFSET = 61;
    var DIGIT_OFFSET = 48;

    function trueChr(integer) {
      if (integer < 10) {
        return String.fromCharCode(integer + DIGIT_OFFSET);
      } else if ((10 <= integer) && (integer <= 35)) {
        return String.fromCharCode(integer + UPPERCASE_OFFSET);
      } else if ((36 <= integer) && (integer <= 62)) {
        return String.fromCharCode(integer + LOWERCASE_OFFSET);
      } else {
        throw 'invalid';
      }

    }

    if (integer === 0) {
      return '0';
    }

    var string = '';
    var remainder;

    while (integer > 0) {
      remainder = Math.floor(integer % BASE);
      string = trueChr(remainder) + string;
      integer = Math.floor(integer / BASE);
    }

    return string;

  }

  function secondsToMinutes(s) {
    s = Math.floor(s);
    var over, minutes;

    if (s < 60) {
      return s + 's';
    }

    if (s < (60 * 60)) {

      over = s % 60;
      minutes = (s - over) / 60;

      return minutes + 'min ' + over + 's';

    }

    var overHour = s % 3600;
    var hours = (s - overHour) / 3600;

    over = (s - (hours * 3600)) % 60;
    minutes = (s - (hours * 3600) - over) / 60;

    return hours + 'h ' + minutes + 'min ' + over + 's';

  }

  app.factory('IdentityStorage', ['$http', function($http) {
    return {
      get: function() {
        return $http({
          url: (window.host || '') + '/api/user/identity/',
          method: 'get'
        });
      }
    };
  }]);


  app.factory('GateStorage', ['$http', function($http) {
    return {
      send: function(data) {
        return $http({
          url: (window.host || '') + '/api/gate/',
          method: 'post',
          data: JSON.stringify(data)
        });
      }
    };
  }]);

  app.factory('GenericGateStorage', ['$http', function($http) {
    return {
      send: function(data) {
        return $http({
          url: (window.host || '') + '/api/generic-gate/',
          method: 'post',
          data: JSON.stringify(data)
        });
      }
    };
  }]);

  app.controller('OutputController', ['$scope', 'IdentityStorage', function($scope, IdentityStorage) {

    IdentityStorage.get().then(function(data) {
      window.PB.userId = data.data.user_id;
      window.seenGate = data.data.seen[window.publicationId];
      window.seenPages = data.data.seen_pages[window.publicationId];
      $scope.$root.$broadcast('identity');
    });

    $scope.iframeCallbacks = {};
    $(window).resize(function() {
      $scope.$broadcast('resize');
    });

    window.EventBus.register('publication', function(data, e) {
      iframeMessageEvent = e;
      sendHeightUpdate();
    });

    window.EventBus.register('embed', function(e) {
      var callback = $scope.iframeCallbacks[e.id];

      if (callback) {
        callback(e);
      }
    });
  }]);

  app.controller('GateController', ['$scope', 'GateStorage', '$sce', function($scope, GateStorage, $sce) {
    $(function() {
      var block = $('#block-' + window.conf.block);
      var t = block.text();

      if (t.length > 297) {
        t = t.substring(0, 297);  // grab the first 297 chars
        t = t + '...';
      }

      $scope.preview = t;
      $scope.$apply();
    });

    $scope.submit = function() {
      if ($scope.name && $scope.email) {
        GateStorage.send({
          email: $scope.email,
          name: $scope.name,
          block_id: window.conf.block,
          publication: {pk: window.publicationId},
          referrer: document.referrer,
          anonymous_id: window.analytics.user().anonymousId()
        }).then(function() {
          gateFilled = true;
          $.magnificPopup.instance.close();
        });
      }
      return false;
    };
  }]);

  app.controller('CreditController', ['$scope', 'GateStorage', function($scope, GateStorage) {

    $scope.submit = function() {
      if ($scope.email) {
        GateStorage.send({
          name: '',
          email: $scope.email,
          block_id: window.conf.block,
          publication: {pk: window.publicationId},
          referrer: document.referrer
        }).then(function() {
          gateFilled = true;
          $.magnificPopup.instance.close();
        });
      }
      return false;
    };
  }]);

  function getBlockIdFromRange(range) {
    var parent = range.commonAncestorContainer.parentNode;

    while (parent.className.indexOf('text-block') == -1) {
      parent = parent.parentNode;
    }

    return parent.id.split('-')[1];

  }

  function clearSelection() {
    if (window.getSelection) {
      if (window.getSelection().empty) {  // Chrome
        window.getSelection().empty();
      } else if (window.getSelection().removeAllRanges) {  // Firefox
        window.getSelection().removeAllRanges();
      }
    } else if (document.selection) {  // IE?
      document.selection.empty();
    }
  }

  function sendHeightUpdate() {
    if (!iframeMessageEvent) {
      return;
    }

    if (heights.length > 5) {
      var lastFive = heights.slice(-5);
      var same = _.every(lastFive, function(el) {
        return el === lastFive[0];
      });

      if (same) {
        clearInterval(interval);
      }
    }

    var message = {};
    var blockId = iframeMessageEvent.data.blockId;

    if (blockId) {
      var $block = $('#block-' + blockId);
      message.blockOffset = $block.offset().top;
    }

    message.height = $(document).height();
    heights.push(message.height);
    iframeMessageEvent.source.postMessage(message, iframeMessageEvent.origin);

    if (!interval) {
      interval = setInterval(function() {
        sendHeightUpdate();
      }, 200);
    }

  }

  app.directive('iframe', [function() {
    return {
      restrict: 'E',
      link: function(scope, elem, attrs) {
        var iframe = elem[0];
        var id = iframe.src.split('/').reverse()[0];

        iframe.onload = function() {
          iframe.contentWindow.postMessage('send', iframe.src);
        };

        scope.iframeCallbacks[id] = function(data) {
          iframe.height = data.height + 'px';
        };
      }
    };
  }]);

  app.directive('imageLoaded', [function() {
    return {
      restrict: 'A',
      link: function(scope, elem, attrs) {
        elem.bind('load', function() {
          sendHeightUpdate();
        });
      }
    };
  }]);

  app.directive('modal', ['$window', function ($window) {
    return {
      link: function(scope, elem, attrs) {
        if (elem.hasClass('shareable')) {

        } else {

          if (elem.hasClass('gallery')) {
            elem.each(function() {
              $(this).magnificPopup({
                delegate: '.gallery__item a.popup',
                type: 'image',
                gallery: {
                  enabled: true
                }
              });
            });
          } else {
            elem.magnificPopup({type:'image'});
          }
        }
      }
    };
  }]);

  app.directive('block', ['$window', function($window) {
    return {
      link: function(scope, elem, attrs) {
        var blockAttrs = JSON.parse(attrs.block);

        function updateFullImageSize() {
          var baseWidth;

          if (window.PB.isPlatfora) {
            baseWidth = $(elem).parent().innerWidth();
          } else {
            baseWidth = $(elem).parent().width();
          }

          $(elem).css({
            width: $window.innerWidth + 'px',
            right: 'auto',
            marginLeft: '-' + ($window.innerWidth - baseWidth) / 2 + 'px'
          });
        }

        if (blockAttrs.alignment == '1') {  // full alignment
          updateFullImageSize();
          scope.$on('resize', updateFullImageSize);
        }

      }
    };
  }]);

  $(function() {

    // Select text to share via Twitter

    var popup = $('#selection-popup');
    var twitterShare = {};

    window.addEventListener('mouseup', function(e) {

      var quote = null;
      var url = null;
      var blockId = null;
      var selection = window.getSelection();

      if (!selection.toString()) {
        popup.hide();
        return;
      }

      popup.css({
        left: e.pageX + 'px',
        top: e.pageY + 'px'
      });

      popup.show();

      twitterShare.quote = selection.toString();
      twitterShare.quote = twitterShare.quote.substring(0, 120);

      blockId = getBlockIdFromRange(selection.getRangeAt(0));

      if (blockId) {
        twitterShare.url = 'http://' + window.shortHost + '/t' + decode(blockId);
      } else {
        twitterShare.url = window.location.href;
      }

    });

    popup.click(function() {
      clearSelection();

      var href = 'https://twitter.com/intent/tweet?text=' +
      twitterShare.quote + '&url=' + twitterShare.url;

      window.open(href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');
      popup.hide();
    });

    // Shareable blocks
    $('.shareable').on('click', function() {
      var sc = $(this).find('.shareable-content');
      $.magnificPopup.open({
        items: {
          type: 'inline',
          src: sc
        }
      });
      return false;
    });

    // Mobile nav
    $('[data-js="mobile-nav"]').click(function() {
      if($('.share-menu').hasClass('active')) {
        $('.share-menu').removeClass('active');
      }
      $('header nav').toggleClass('active');
      return false;
    });
    // Hide mobile nav when you click outside the dropdown area
    $('html').click(function() {
      $('header nav').removeClass('active');
    });
    $('.dropdown').click(function(event) {
      event.stopPropagation();
    });

    // Mobile share menu
    $('[data-js="share-toggle"]').click(function() {
      if($('header nav').hasClass('active')) {
        $('header nav').removeClass('active');
      }
      $('.share-menu').toggleClass('active');
      return false;
    });

    // Share menu tabs
    var tabContainers = $('.share-menu > div');
    tabContainers.hide().filter(':first').show();
    $('.share-menu__tabs a').click(function() {
      tabContainers.hide();
      tabContainers.filter(this.hash).show();
      $('.share-menu__tabs a').removeClass('selected');
      $(this).addClass('selected');
      return false;
    }).filter(':first').click();

    // Flexslider
    $(window).load(function() {
      $('.flexslider').flexslider({
        animation: "slide",
        start: function(slider){
          $('body').removeClass('loading');
        }
      });
    });

    function initGate() {
      var items = {
        src: '#gate'
      };

      if (window.seenGate) {
        return;
      }

      if (window.gateType === 's') {
        $.magnificPopup.open({
          modal: true,
          items: items
        });
      }

      if (window.gateType === '1') {

        setTimeout(function() {
          if (gateFilled) {
            return;
          }

          var copyPlaceholder = $('#credit-copy');
          var text;

          if (window.conf.block) {
            var article = window.PB.blockToArticle[window.conf.block];
            text = window.PB.articleCopy[article] || '';
          } else {
            text = window.PB.defaultCopy;
          }

          text = text.replace('\n', '<br>');
          copyPlaceholder.html(text);

          $.magnificPopup.open({
            modal: true,
            items: {
              src: '#credit'
            },
            mainClass: 'mfp-move-from-bottom'
          });
        }, 20 * 1000);

      }

      if (window.gateType === 'd') {
        setTimeout(function() {
          window.addEventListener('scroll', function() {
            if (gateFilled) {
              return;
            }

            $.magnificPopup.open({
              closeMarkup: '<button title="%title%" class="mfp-close">CLOSE<i class="mfp-close-icn">&times;</i></button>',
              items: items
            });
          });
        }, 2000);

      }

      if (window.gateType === 'o') {
        $.magnificPopup.open({
          closeMarkup: '<button title="%title%" class="mfp-close">CLOSE<i class="mfp-close-icn">&times;</i></button>',
          items: items
        });
      }
    }

    // Google Analytics events

    function path($e) {
      var path_separator = ' > ';
      var prts = [];
      var last = $e.data('ga');
      var $parents = $e.parents();

      if (last == 'download-button' || last == 'download-link') {
        var filepath = $e.attr('href');
        var findex = filepath.lastIndexOf('/');

        if (findex != -1) {
          var filename = filepath.slice(findex+1);
          last = last + path_separator + filename;
        }
      }

      if (typeof last === 'undefined') {
        last = $e.text().trim();
      }

      if (typeof last !== 'undefined') {
        prts.push(last);
      }

      $parents.each(function() {
        var $this = $(this);
        var dak = $this.data('ga');
        if (typeof dak !== "undefined") {
          prts.push(dak);
        }
      });

      prts.reverse();

      return prts.join(path_separator);
    }

    function gaEventHandler(event) {
      // get label value from data attribute
      var $this = $(this);
      var p = path($this);
      var shouldRedirect = true;

      if (p === 'publet-image-trigger') {
        shouldRedirect = false;
      }

      var href = $this.attr('href');
      window.ga('send', 'event', 'button', 'click', p);

      if (typeof href !== 'undefined' && href != '#') {
        // if a link
        if (href.slice(0,4) == 'http' && href.indexOf(window.location.hostname) == -1) {
          // if outbound
          window.ga('send', 'event', 'outbound', 'click', href, {'hitCallback': function () {
            if ($this.attr('target') == '_blank'){
              // for blank we don't need todo any redirection
            } else {
              if (shouldRedirect) {
                document.location = href;
              }
            }
          }});
        } else {
            // if internal
        }
      }
    }

    setTimeout(function() {
      $('.ga').on('click', gaEventHandler);
    }, 1000);

    initGate();

    // Heatmap

    function getHeatmapLegend() {
      if (!window.PB.heatmap) {
        return;
      }

      function scale(n) {
        var f = 50;
        n = 100 - n;
        var ratio = 100 / f;
        var new_n = n / ratio;
        var offset = (100 - f) / 2;
        return new_n + offset;
      }

      function hsla(percent) {
        var value;
        var alpha = '0.75';

        if (percent === 0) {
          alpha = 0;
          value = 0;
        } else {
          value = scale(percent);
        }

        return {
          percent: percent,
          color: 'hsla(0, 100%, ' + value + '%, ' + alpha + ')'
        };
      }

      function makeDiv(obj) {
        var div;

        if (_.contains([25, 50, 75], obj.percent)) {
          div = $('<div>' + obj.percent + '%</div>');
        } else {
          div = $('<div />');
        }

        return div.css({
          backgroundColor: obj.color,
          textAlign: 'center',
          color: '#fff',
          width: '100px',
          height: '5px',
          display: 'block'
        });
      }

      var colorDivs = _.map(_.range(0, 100), _.compose(makeDiv, hsla));
      var container = $('<div />').css({
        position: 'fixed',
        top: (($(window).height() - 500) / 2) + 'px',
        left: '20px'
      }).append(colorDivs);
      $('body').append(container);

    }

    function runHeatmap() {
      if (!window.PB.heatmap) {
        return;
      }

      var $body = $('body');

      _.each(window.PB.heatmap, function(obj, key) {
        var $block = $('#block-' + key);

        if (!$block.length) {
          return true;
        }

        var width = $block.width();
        var height = $block.height();
        var top = $block.offset().top;
        var left = $block.offset().left;

        var $div = $('<div class="heatmap-box" style="' + obj.css + '"><span>'+ secondsToMinutes(obj.seconds) + '</span></div>');

        $div.css({
          width: width + 'px',
          height: height + 'px',
          top: top + 'px',
          left: left + 'px'
        });

        $body.append($div);
      });

    }

    setTimeout(function() {
      runHeatmap();
      getHeatmapLegend();
    }, 2000);

  });

  // Export the app.
  window.app = app;

}(jQuery));
