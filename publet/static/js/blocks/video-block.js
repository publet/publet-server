(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  app.directive('videoBlock', [function() {
    // Note: The scope of this directive is shared with the `block` directive.
    return {
      restrict: 'A',
      link: function(scope, elm, attrs) {
        scope.show_player = false;
        scope.show_preview = false;
        scope.video_type = scope.block.video_type;

        var TEXT_ALIGNMENTS = {
          'l': 'left',
          'r': 'right',
          'c': 'center'
        };

        /*
         * Functions {{{
         */
        scope.findVideoTypeFromBlock = function() {
          return scope.video_type;
        };

        scope.style = function() {
          var css = [];

          if (scope.block.font) {
            var f = scope.fontsByUrl[scope.block.font];
            css.push(f.css);
          }

          if (scope.block.color) {
            var c = scope.colorsByUrl[scope.block.color];
            css.push('color: ' + c.color);
            css.push('background-color: ' + c.background_color);
          }

          if (scope.block.size) {
            css.push('font-size: ' + scope.block.size + 'px');
            css.push('line-height: ' + scope.block.line_height + 'em');
          }

          if (scope.block.text_alignment) {
            css.push('text-align: ' + TEXT_ALIGNMENTS[scope.block.text_alignment]);
          }

          return css.join('; ');
        };

        scope.previewClick = function() {
          scope.show_player = true;
          scope.show_preview = false;
        };

        scope.$blockScope.isEmpty = function videoBlockIsEmpty() {
          return scope.block.video_url.length !== 0? false: true;
        };
        // }}}

        scope.$watch('block.video_url', function(newVideoUrl, oldVideoUrl) {
          if (oldVideoUrl !== newVideoUrl) {
            scope.video_type = app.getVideoType(newVideoUrl);
            scope.$broadcast('video-url-changed');
            scope.$root.$broadcast('block-contents-changed');
          }
        });

        scope.$watch('block.alignment', function(newValue, oldValue) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
          }
        });

        scope.$watch('block.size', app.changeHandler);
        scope.$watch('block.alignment', app.changeHandler);
        scope.$watch('block.text_alignment', app.changeHandler);
        scope.$watch('block.color', app.changeHandler);
        scope.$watch('block.line_height', app.changeHandler);
        scope.$watch('block.has_caption', app.changeHandler);

        if (scope.block.preview_url) {
          scope.show_preview = true;
        } else {
          scope.show_player = true;
        }

      }
    };
  }]);

})(window);
