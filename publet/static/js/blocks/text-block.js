(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  app.directive('textBlock', ['AssetStorage', 'SaveService', function(AssetStorage, SaveService) {
    // Note: The scope of this directive is shared with the `block` directive.
    return {
      restrict: 'A',
      link: function(scope, elm, attrs) {

        // When a text block is marked as an embed, we display the content
        // inside an iframe for security reasons.  The iframe's source is
        // something like /iframe/1234 where 1234 is the block's id.  But of
        // course, the parent page (in this case the block editor) has no idea
        // how tall the content inside the iframe is.  Since the iframe is on
        // the same domain as the editor, we can use contentWindow
        // communication to obtain that information.
        //
        // We send a message to the iframe and register a callback on
        // ArticleController.  Once the message comes back from the iframe, the
        // controller will look up the stored callback and call it with the
        // height of the content inside the iframe.

        var iframeRegistered = false;

        var TEXT_ALIGNMENTS = {
          'l': 'left',
          'r': 'right',
          'c': 'center'
        };

        function registerIframeHandler() {
          if (iframeRegistered) {
            return;
          }

          var holder = $(elm).find('.iframe-holder');
          var f = $('<iframe width="100%" frameborder="0" src="/iframe/' + scope.block.id + '">');
          holder.replaceWith(f);

          scope.iframe = $(elm).find('iframe')[0];

          scope.iframe.onload = function() {
            scope.iframeCallbacks[scope.block.id] = function(height) {
              scope.iframe.height = height + 'px';
            };
            scope.iframe.contentWindow.postMessage('{}', scope.iframe.src);
          };

          iframeRegistered = true;
        }

        scope.chooseAsset = function() {
          var settings = angular.copy(window.FP.write);
          settings.multiple = true;
          filepicker.pickAndStore(settings, {}, function(fpfiles) {
            // TODO: We should really be adding these images all at once.
            // However, tastypie doesn't seem to provide that functionality.
            $.map(fpfiles, function(el, i) {
              AssetStorage.addAsset(scope.block, el.url).then(function(response) {
                scope.block.assets.push(response.data);
              });
            });
            scope.$apply();
          });
        };

        scope.removeAsset = function(asset) {
          AssetStorage.removeAsset(asset).then(function() {
            scope.block.assets.some(function(a, key) {
              if (a.resource_uri === asset.resource_uri) {
                scope.block.assets.splice(key, 1);
              }
            });
          });
        };

        scope.style = function() {

          // This function is called many times for a single element so if the
          // fontsByUrl object isn't populated, we can just try again next
          // time.
          if (!scope.fontsByUrl) {
            return;
          }

          if (!scope.colorsByUrl) {
            return;
          }

          var css = [];

          if (!scope.flavorObject) {
            scope.flavorObject = scope.getCurrentFlavorObject();
          }

          var fo = scope.flavorObject;

          if (scope.block.font) {
            var f = scope.fontsByUrl[scope.block.font];
            if (f) {
              css.push(f.css);
            }
          } else if (fo && fo.font && fo.font.css) {
            css.push(fo.font.css);
          }

          if (scope.block.color) {
            var c = scope.colorsByUrl[scope.block.color];
            if (c && c.hex) {
              css.push('color: #' + c.hex);
            }
          } else if (fo && fo.color && fo.color.hex) {
            css.push('color: #' + fo.color.hex);
          }

          if (scope.block.background_color) {
            var bc = scope.colorsByUrl[scope.block.background_color];
            if (bc && bc.hex) {
              css.push('background-color: #' + bc.hex);
            }
          } else if (fo && fo.background_color && fo.background_color.hex) {
            css.push('background-color: #' + fo.background_color.hex);
          }

          if (scope.block.size) {
            css.push('font-size: ' + scope.block.size + 'px');
          } else if (fo && fo.size) {
            css.push('font-size: ' + fo.size + 'px');
          }

          if (scope.block.line_height) {
            css.push('line-height: ' + scope.block.line_height + 'em');
          } else if (fo && fo.line_height) {
            css.push('line-height: ' + fo.line_height + 'em');
          }

          if (scope.block.text_alignment) {
            css.push('text-align: ' + TEXT_ALIGNMENTS[scope.block.text_alignment]);
          } else if (fo && fo.text_alignment) {
            css.push('text-align: ' + TEXT_ALIGNMENTS[fo.text_alignment]);
          }

          if (scope.block.alignment === '1') {
            css.push('width: ' + window.innerWidth + 'px');
            css.push('margin-left: -' + (window.innerWidth - 700) / 2 + 'px');
          }

          return css.join('; ');
        };

        // Text can be treated as ready as soon as possible because we don't
        // need to wait for any external assets to load (like images)
        scope.checkIfTextReady = function() {
          return true;
        };

        scope.textBlockReady = function() {
          scope.$root.$broadcast("blockLoaded");

          // TODO: detect content loaded when text is in an iframe.
          // TODO: Don't use iframes, if any!
        };

        scope.$blockScope.isEmpty = function textBlockIsEmpty() {
          //return $(elm).find('.text-block-preview').text().trim().length !== 0? false: true; // Don't consider white space padding.
          return $(elm).find('.text-block-preview').text().length !== 0? false: true; // Consider white space padding.
        };

        scope.$watch('block.size', app.changeHandler);
        scope.$watch('block.line_height', app.changeHandler);
        scope.$watch('block.is_bullets', app.changeHandler);
        scope.$watch('block.is_indented', app.changeHandler);
        scope.$watch('block.alignment', app.changeHandler);
        scope.$watch('block.background_color', app.changeHandler);
        scope.$watch('block.text_alignment', app.changeHandler);

        scope.$watch('block.is_embed', function(newValue, oldValue) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
          }

          if (oldValue || newValue) {
            registerIframeHandler();
          }

        });

        $(function() {
          // This is done here because there is no simple way of delegating the
          // calling of a plugin on an element.
          $(elm).find('span a').tooltip();
        });

      }
    };
  }]);

})(window);
