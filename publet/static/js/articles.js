(function(window) {

  var BLOCKTYPEMAP = {
    photo: 'photoblocks',
    text: 'textblocks',
    video: 'videoblocks',
    audio: 'audioblocks'
  };

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  // Filters.
  app.filter('linebreaksbr', function() {
    return function(text) {

      if (!text) { return; }

      // Escape HTML first.
      text = text.replace(/&/g, '&amp;').replace(/>/g, '&gt;')
      .replace(/</g, '&lt;');

      return text.replace(/\n/g, '<br />');
    };
  });
  app.filter('sanitize', function() {
    return function(text) {

      if (!text) { return; }

      return text.replace(/<br>/g, '\n');
    };
  });

  app.filter('capitalize', function() {
    return function(input, scope) {
      if (input !== null) {
        input = input.toLowerCase();
      }
      return input.substring(0,1).toUpperCase() + input.substring(1);
    };
  });

  // Controllers.
  app.controller('ArticleController',
                 ['$scope', '$timeout', 'BlockStorage', 'ArticleStorage', 'PublicationStorage', 'TypeStorage', 'ThemeStorage', '$location', 'SaveService', '$sce', '$q', '$rootScope',
                 function($scope, $timeout, BlockStorage, ArticleStorage, PublicationStorage, TypeStorage, ThemeStorage, $location, SaveService, $sce, $q, $rootScope) {

    $scope.features = window.PB.features;
    $scope.featureActive = function(f) {
      // TODO Add more rules
      var feature = $scope.features[f];

      if (feature === undefined) {
        return false;
      }

      if (!feature.is_active) {
        return false;
      }

      return true;

    };

    $scope.cannedAnalysisShowing = false;

    $scope.showCannedAnalysis = function(e) {
      var $overlay = $('#canned-demo-overlay');

      if ($scope.cannedAnalysisShowing) {
        $scope.cannedAnalysisShowing = false;
        $overlay.hide();
      } else {
        $scope.cannedAnalysisShowing = true;
        var $button = $(e.target);
        var offsetTop = $button.offset().top;
        var width = ($(window).width() - 500) / 2;

        $overlay.css({
          top: offsetTop + 50 + 'px',
          left: width + 'px',
          display: 'block'
        });
      }
    };

    $scope.useLoadScreen = true;
    $rootScope.saveNowText = 'Save now';
    $scope.$root.cache = {
      article: null,
      publication: null,
      group: null,
      theme: null
    };

    var countBlocksLoaded = 0;
    $scope.editingBlock = {}; // When we load up a article, we're not editing a block.
    $scope.savingArticle = '';
    $scope.lastModified = null;
    $scope.static = window.static;
    $scope.draftModeEnabled = window.draft_mode_enabled;
    $scope.formatColorCell = app.formatColorCell;
    $scope.escapeMarkup = app.escapeMarkup;
    $scope.select2Options = app.select2Options;
    $scope.loading = true;

    // iframe sizing
    $scope.iframeCallbacks = {};

    $scope.linkText_zip = 'Download HTML';
    $scope.linkText_pdf = 'Download PDF';
    $scope.linkText_epub = 'Download ePub';
    $scope.linkText_mobi = 'Download MOBI';

    $scope.url_zip = '';
    $scope.url_pdf = '';
    $scope.url_epub = '';
    $scope.url_mobi = '';

    $scope.select2Options = {
      dropdownAutoWidth: true
    };

    $scope.deleteState = {
      deletingBlock: false,
      blockToBeDeleted: null,
      originalDeleteEvent: null
    };

    $scope.saveNow = function() {
      $scope.$root.$broadcast('block-contents-changed');
    };

    // iframe sizing
    function iframeMessageHandler(event) {
      if (typeof event.data === 'object') {
        var callback = $scope.iframeCallbacks[event.data.id];

        if (callback) {
          callback(event.data.height);
        }
      }
    }

    $scope.trust = function(html) {
      return $sce.trustAsHtml(html);
    };

    $scope.compileBlocks = function() {
      var blocks = [];

      var photoblocks      = $scope.article.photoblocks;
      var textblocks       = $scope.article.textblocks;
      var videoblocks      = $scope.article.videoblocks;
      var audioblocks      = $scope.article.audioblocks;

      blocks = blocks.concat(
        photoblocks,
        textblocks,
        videoblocks,
        audioblocks
      );

      var sorted = blocks.slice(0).sort(function(a, b) {
        return a.order - b.order;
      });

      var sortedBlocks = [];

      for (var i = 0, len = sorted.length; i < len; ++i) {

        var obj, prev, next;

        prev = sorted[i - 1];
        next = sorted[i + 1];

        if (prev) {
          prev = {
            type: prev.type
          };
        }

        if (next) {
          next = {
            type: next.type
          };
        }

        obj = sorted[i];
        obj.prev = prev;
        obj.next = next;

        sortedBlocks[i] = obj;

      }

      $scope.blocks = sortedBlocks;
    };

    $scope.addBlock = function(type, block, content) { // See "insertion line events" in interface.js
      $scope.$root.$broadcast('close-all-blocks');

      block = block || {order: -1};

      var order = block.order + 1;
      var afterBlocks = [];

      // Collect the blocks that are before and after the currently-
      // editing block.
      for (var i = 0; i < $scope.blocks.length; i++) {
        if ($scope.blocks[i].order >= order) {
          afterBlocks.push($scope.blocks[i]);
        }
      }

      // Move the after-blocks up one.
      afterBlocks.forEach(function(block) {
        block.order = block.order + 1;
      });

      var saveCall;

      if (type === 'text') {
        saveCall = BlockStorage.addTextBlock($scope.article, order, content);
      } else {
        saveCall = BlockStorage.addBlock(type, $scope.article, order);
      }

      saveCall = saveCall.then(function(response) {

        var blockType = BLOCKTYPEMAP[type];
        var block = response.data;

        // The isNew value is used for setting the block into edit mode when
        // it's first added
        block.isNew = true;

        $scope.article[blockType].push(block);
        $scope.compileBlocks();

        return response;

      });

      saveCall.then(function(response) {
        return $scope.save(); // returns promise
      });

      return saveCall;
    };

    $scope.removeBlock = function($event, block) {
      $scope.deleteState.deletingBlock = true;
      $scope.deleteState.blockToBeDeleted = block;
      $scope.deleteState.originalDeleteEvent = $event;
      return false;
    };

    $scope._removeBlock = function() {
      var $event = $scope.deleteState.originalDeleteEvent;
      var block = $scope.deleteState.blockToBeDeleted;

      $event && $event.stopPropagation();
      $scope.deleteState.originalDeleteEvent = null;

      var blockType = BLOCKTYPEMAP[block.type];

      for (var i = 0; i < $scope.article[blockType].length; i++) {
        if (block.id === $scope.article[blockType][i].id) {
          $scope.article[blockType].splice(i, 1);
          countBlocksLoaded--; // Note: this is incremented on blockLoaded
        }
      }

      $scope.compileBlocks();

      // If the old block was the same as the "currently editing" block, reset it.
      if ($scope.editingBlock == block) {
        $scope.editingBlock = {};
      }

      return BlockStorage.removeBlock(block).then(function(response) {
        $scope.deleteState.deletingBlock = false;
        $scope.save();
      });
    };

    $scope.mergeWithPrevious = function(block) {

      if (block.type !== 'text' || !block.prev) {
        return;
      }

      if (block.prev.type !== 'text') {
        return;
      }

      var prev = $scope.blocks[block.order - 1];

      prev.content = prev.content + block.content;

      $scope.removeBlock(null, block);
    };

    $scope.deleteArticle = function(article) {
      ArticleStorage.deleteArticle(article).then(function(response) {
        window.location = '/groups/';
        $scope.$apply();
      });
    };

    $scope.getType = function() {
      TypeStorage.getType().then(function(response) {
        $scope.types = response.data.objects;
      });
    };

    $scope.getThemes = function() {
      ThemeStorage.getThemes().then(function(response) {
        $scope.themes = response.data.objects;
        $scope.fontsByUrl = {};
        $scope.colorsByUrl = {};

        var t, f, c;

        for (var i = 0; i < $scope.themes.length; i++) {
          t = $scope.themes[i];

          for (var k = 0; k < t.fonts.length; k++) {
            f = t.fonts[k];
            $scope.fontsByUrl[f.resource_uri] = f;
          }

          for (var j = 0; j < t.colors.length; j++) {
            c = t.colors[j];
            $scope.colorsByUrl[c.resource_uri] = c;
          }
        }

      });
    };

    $scope.save = function(form) {
      $scope.$root.$broadcast('order-blocks');
      return SaveService.save(form ? form : null, ArticleStorage.saveArticle, $scope.article); // return a promise
      // FIXME: ^ if a second argument to SaveService.save is *not* a promise,
      // then the promise gets broken. This needs better design. We shouldn't
      // let a consumer of a promiseed function accidentally break the chain.
      // See FIXME in SaveService.save in save.js.
    };

    $scope.renderPublication = function(extension) {
      if ($scope['url_' + extension]) {
        return true;
      }

      $scope['linkText_' + extension] = 'Please wait...';

      var interval;

      function checker() {
        PublicationStorage.renderPublication($scope.publication, extension).then(function(response) {
          if (response.data.status === 'ready') {
            clearInterval(interval);
            $scope['linkText_' + extension] = 'Done! Click to download.';
            $scope['url_' + extension] = response.data.path;
          }
        });
      }

      interval = setInterval(checker, 5000);
      checker();

      return false;
    };

    $scope.getAlignmentClassForBlock = function(block) {
      if (block.type === 'photo') {

        if (block.alignment === '3') {
          return 'align-breaking-left-photo';
        }

        if (block.alignment === '4') {
          return 'align-breaking-right-photo';
        }

      }

      if (block.alignment === null) {
        return 'align-column';
      }

      return app.alignmentClasses[block.alignment];
    };

    window.addEventListener('message', iframeMessageHandler, false);
    window.addEventListener("beforeunload", function (e) {
      if (!$scope.savingDisabled) {
        return;
      }

      var confirmationMessage = "A save is in progress.";

      (e || window.event).returnValue = confirmationMessage;
      return confirmationMessage;
    });

    if ($scope.useLoadScreen) {
      $scope.$on('blockLoaded', function() {
        $scope.$evalAsync(function() {
          countBlocksLoaded++; // Note: this is decremented in _removeBlock

          if (countBlocksLoaded == $scope.blocks.length) { // when all blocks loaded.

            //clear empty blocks if any, and if no blocks are left add a default block.
            // This is coupled to the addBlock code because we're relying on the fact that
            // an article will always have some block associated with it since blocks are created in the DB
            // before being created in the front end, and thus if the user refreshes the browser,
            // the block will exist in the article even if it's empty despite our attempt to
            // prevent the article from having empty blocks, so we thus rely on this blockLoaded event
            // to check for empty blocks and clean them up. See addBlock.
            $scope.cleanup();

            if (!$scope.blocks.length) { // if no blocks
              $scope.addBlock('text').then(function(response) {});
            } else {
              $scope.loading = false;
            }
          }
        });
      });
    } else {
      $timeout(function() {
        $scope.loading = false;
      }, 2500);
    }

    $scope.cleanup = function() {
      var $blocks = $('div[block]');

      for (var i = 0, len = $scope.blocks.length; i < len; i+=1) {
        var blockScope = angular.element($blocks.eq(i).get(0)).scope();

        if (blockScope.isEmpty() && !blockScope.block.isNew) {
          $scope.deleteState.blockToBeDeleted = blockScope.block;
          $scope._removeBlock();
        }
      }
    };

    $scope.$watch('article', function() {
      // When the article object changes, we need to recompile all of the
      // individual blocks into one group to render to the canvas.
      if ($scope.article) {
        $scope.compileBlocks();
        if (!$scope.blocks.length) {
          $scope.addBlock('text');
        }
      }
    });

    $scope.getIntegrations = function() {
      if (!$scope.integrationsList) {
        $scope.integrationsList = _.map(window.PB.integrations, function(v, k) {
          return {
            slug: k,
            name: v
          };
        });
      }

      return $scope.integrationsList;
    };

    $scope.submitToIntegration = function() {
      BlockStorage.submitToIntegration($scope.integrationBlock, $scope.integration);
      $scope.integrationBlock = null;
      $scope.integration = null;
    };

    $scope.hideSubmitToIntegration = function() {
      $scope.selectingIntegration = false;
    };

    $scope.getType();
    $scope.getThemes();
  }]);

  // Directives.
  app.directive('article',
                ['GroupStorage', 'ArticleStorage', 'PublicationStorage', 'FlavorStorage', 'SaveService', '$timeout', '$rootScope',
                function(GroupStorage, ArticleStorage, PublicationStorage, FlavorStorage, SaveService, $timeout, $rootScope) {
    return {
      compile: function compile(elm, attrs, transclude) {
        return {
          post: function post(scope, elm, attrs) {
            // Once we've compiled the article directive, we need to hit the
            // API to get the data for this article.

            // Note that the group and especially its colors need to be loaded
            // before the articles starts to get rendered.  There are certain
            // kinds of blocks that depend on this information at runtime.

            scope.article = $rootScope.cache.article;
            scope.group = $rootScope.cache.group;
            scope.publication = $rootScope.cache.publication;
            scope.theme = $rootScope.cache.theme;

            if (!scope.article) {
              GroupStorage.getGroup(window.group_id).then(function(response) {
                scope.group = response.data;
                $rootScope.cache.group = scope.group;
              }).then(function() {

                ArticleStorage.getArticle(window.article_id).then(function(response) {
                  scope.article = response.data;
                  scope.theme = scope.article.theme;
                  scope.allFlavors = window.allFlavors;

                  $rootScope.cache.article = scope.article;
                  $rootScope.cache.theme = scope.article.theme;
                  $rootScope.articleLastModified = response.data.modified;
                });

              });

              PublicationStorage.getPublicationWithFlatArticles(window.publication_id).then(function(response) {
                scope.publication = response.data;
                $rootScope.cache.publication = scope.publication;
              });

            }

            scope.$root.$on('block-contents-changed', function() {
              scope.$evalAsync(function() {
                scope.save();
              });
            });
            scope.$root.$on('order-blocks', function() {
              var $blocks = $('div.block');

              // Set order on blocks according to where they are in the DOM.
              for (var i = 0; i < $blocks.length; i++) {
                var blockScope = angular.element($blocks.eq(i).get(0)).scope();
                blockScope.block.order = i;
              }

            });

            // Sortable blocks.
            $('div#blocks-container').sortable({
              handle: '[data-js="reorder"], div.block-controls',
              start: function(event, ui) {
                var itemHeight = ui.item.height();
                $('div.ui-sortable-placeholder').height(itemHeight);
              },
              sort: function(event, ui) {
              },
              stop: function(event, ui) {
                $rootScope.$evalAsync(function() {
                  $rootScope.$broadcast('order-blocks');
                });
                SaveService.save(null, ArticleStorage.reorderArticle, scope.article).then(function (response) {
                  $rootScope.savingDisabled = false;
                  $rootScope.saveStatus = '';
                  $rootScope.articleLastModified = response.data.modified;
                  // TODO: re-order DOM and set order properties based on response
                });
              }
            });

          }
        };
      }
    };
  }]);

})(window);
