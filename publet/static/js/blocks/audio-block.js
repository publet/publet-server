(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // SoundCloud

  // TODO: What even is this?
  SC.initialize({
    client_id: 'YOUR_CLIENT_ID'
  });

  // Get the app.
  var app = window.app;

  app.directive('audioBlock', [function() {
    // Note: The scope of this directive is shared with the `block` directive.
    return {
      restrict: 'A',
      link: function(scope, elm, attrs) {
        var countPlayersLoaded = 0;

        var TEXT_ALIGNMENTS = {
          'l': 'left',
          'r': 'right',
          'c': 'center'
        };

        var $input = $(elm).find('input');

        /*
         * Functtions {{{
         */
        var rebuildAudio = function(save) {

          if (save) {
            scope.$root.$broadcast('block-contents-changed');
          }

          var url = scope.block.audio_url;

          var $audio = $(elm).find('div.audio');
          $audio.html('');

          SC.oEmbed(url, function(oembed) {
            $audio.html(oembed ? oembed.html : '');

            // TODO, detect when the player is actually loaded.
            countPlayersLoaded++;
            if (countPlayersLoaded == 1) { // only emit on the first load
              scope.$root.$broadcast('blockLoaded');
            }
          });

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

        scope.saveAudio = function() {
          scope.$root.$broadcast('block-contents-changed');
        };

        scope.$blockScope.isEmpty = function audioBlockIsEmpty() {
          return scope.block.audio_url.length !== 0? false: true;
        };
        // }}}

        scope.$watch('block.size', app.changeHandler);
        scope.$watch('block.alignment', app.changeHandler);
        scope.$watch('block.text_alignment', app.changeHandler);
        scope.$watch('block.color', app.changeHandler);
        scope.$watch('block.line_height', app.changeHandler);
        scope.$watch('block.has_caption', app.changeHandler);

        scope.$watch('block.audio_url', function(oldAudioUrl, newAudioURl) {
          if (oldAudioUrl !== newAudioURl) {
            rebuildAudio(true);
          }
        });

        rebuildAudio();

      }
    };
  }]);

})(window);
