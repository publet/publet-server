(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  // Directives.
  app.directive('photoBlock', ['PhotoStorage', '$rootScope', '$timeout', function(PhotoStorage, $rootScope, $timeout) {
    // Note: The scope of this directive is shared with the `block` directive.
    return {
      restrict: 'A',
      link: function(scope, elm, attrs) {
        var $caption = $(elm).find('textarea');
        var $photosContainer = $(elm).find('.photos-container');
        var newPhotoArray = [];
        var photo;
        scope.part = null;

        scope.availableGridTypes = [
          {value: 'single', label: 'Single Image'},
          {value: 'grid', label: 'Grid'},
          {value: 'slideshow', label: 'Slideshow'},
          {value: 'cover', label: 'Cover'}
        ];

        scope.gridSizes = [
          {value: 2, label: '2'},
          {value: 3, label: '3'},
          {value: 4, label: '4'},
          {value: 5, label: '5'},
          {value: 6, label: '6'}
        ];

        var TEXT_ALIGNMENTS = {
          'l': 'left',
          'r': 'right',
          'c': 'center'
        };

        /*
         * Functions {{{
         */
        scope.sizeInPixels = function(photo) {
          var desired = {
            's': 460,
            'm': 580,
            'l': 700
          }[photo.size];

          if (desired > photo.width) {
            return photo.width;
          } else {
            return desired;
          }

        };

        scope.contentsChanged = function() {
          scope.$root.$broadcast('block-contents-changed');
        };

        scope.choosePhotos = function() {
          var settings = angular.copy(window.FP.write);
          settings.multiple = true;
          filepicker.pickAndStore(settings, {}, function(fpfiles) {
            // TODO: We should really be adding these images all at once.
            // However, tastypie doesn't seem to provide that functionality.
            $.map(fpfiles, function(el, i) {
              PhotoStorage.addPhoto(scope.block, el.url).then(function(response) {
                scope.block.photos.push(response.data);
                scope.$broadcast('photos-updated');
              });
            });
            scope.$apply();
          });
        };

        scope.removePhoto = function(photo) {
          PhotoStorage.removePhoto(photo).then(function() {
            scope.block.photos.some(function(p, key) {
              if (p.resource_uri === photo.resource_uri) {
                scope.block.photos.splice(key, 1);
                scope.$broadcast('photos-updated');
              }
            });
          });
        };

        scope.toggleShadow = function(photo) {
          photo.has_shadow = !photo.has_shadow;
          scope.blur();
        };

        scope.shadowText = function(photo) {
          if (photo.has_shadow) {
            return 'Remove Shadow';
          } else {
            return 'Add Shadow';
          }
        };

        scope.updateAlignment = function(type) {

          if (type === 'grid') {
            scope.ac = [
              {id: '0', name: 'Column'},
              {id: '2', name: 'Breaking'}
            ];
          } else if (type === 'cover') {
            scope.ac = [{id: '1', name: 'Full'}];
          }
          else {
            scope.ac = [
              {id: '0', name: 'Column'},
              {id: '1', name: 'Full'},
              {id: '2', name: 'Breaking'},
              {id: '3', name: 'Breaking left'},
              {id: '4', name: 'Breaking right'},
              {id: '5', name: 'Margin left'},
              {id: '6', name: 'Margin right'}
            ];
          }

        };

        scope.style_cover_title = function() {
          var css = [];

          if (scope.block.cover_font_title) {
            var f = scope.fontsByUrl[scope.block.cover_font_title];
            css.push(f.css);
          }

          if (scope.block.cover_color_title) {
            var c = scope.colorsByUrl[scope.block.cover_color_title];
            if (c && c.hex) {
              css.push('color: #' + c.hex);
            }
          }

          if (scope.block.cover_size_title) {
            css.push('font-size: ' + scope.block.cover_size_title + 'px');
            css.push('line-height: 1.1em');
          }

          return css.join('; ');
        };

        scope.style_cover_subtitle = function() {
          var css = [];

          if (scope.block.cover_font_subtitle) {
            var f = scope.fontsByUrl[scope.block.cover_font_subtitle];
            css.push(f.css);
          }

          if (scope.block.cover_color_subtitle) {
            var c = scope.colorsByUrl[scope.block.cover_color_subtitle];
            if (c && c.hex) {
              css.push('color: #' + c.hex);
            }
          }

          if (scope.block.cover_size_subtitle) {
            css.push('font-size: ' + scope.block.cover_size_subtitle + 'px');
            css.push('line-height: 1.1em');
          }

          return css.join('; ');
        };

        scope.fullPhotoStyle = function(isBlockControls) {
          if (scope.block.alignment != '1') {
            if (!scope.flavorObject || scope.flavorObject.alignment != '1') {
              return '';
            }
          }

          var width = window.innerWidth;

          if (isBlockControls && scope.active) {
            width = '0';
          }

          return 'width: ' + width + 'px; ' + 'right: auto; ' +
            'margin-left: -' + ((window.innerWidth - 700) / 2) + 'px;';
        };

        // Similar to Clojure's partition function
        // partition([1, 2, 3, 4, 5], 2) => [[1, 2], [3, 4], [5]]
        function partition(list, num) {
          num = parseInt(num, 10);
          var a = [];
          var b = [];

          var ends = _.range(0, list.length + 1, num);
          ends.splice(0, 1);

          for (var i = 0; i < list.length; i++) {
            b.push(list[i]);
            if (_.contains(ends, i + 1)) {
              a.push(b);
              b = [];
            }
          }

          if (b.length) {
            a.push(b);
          }

          return a;
        }

        scope.partition = function(list, num) {
          if (scope.part) {
            return scope.part;
          }

          var p = partition(list, num);
          scope.part = p;
          return p;
        };

        scope.$blockScope.isEmpty = function photoBlockIsEmpty() {
          return scope.block.photos.length !== 0? false: true;
        };

        scope.flexSliderImageReady = function(index) {
          $(elm).find('.flex_slider img').eq(index).removeClass('imgNotLoaded');
          $(elm).find('.flex_slider img').eq(index).addClass('imgLoaded');
        };

        scope.flexSliderReadyCheck = function() {
          var numPhotos = scope.block.photos.length;

          // if no photos, we don't need to check for photos being loaded.
          if (!numPhotos) {
            return true;
          }

          // if not all img elements are added to the DOM yet, obviously return false.
          if ($(elm).find('.flex_slider img').length !== numPhotos) {
            return false;
          }

          if ($(elm).find('.flex_slider .imgLoaded').length === numPhotos) {
            return true;
          }

          return false;
        };

        scope.flexSliderReady = function() {
          $(elm).find('.flex_slider').removeClass('flexSliderNotReady');
          $(elm).find('.flex_slider').addClass('flexSliderReady');
          scope.$root.$broadcast('blockLoaded');
        };

        scope.blockImagesImageLoaded = function(index) {
          $(elm).find('.block_images img').eq(index).removeClass('imgNotLoaded');
          $(elm).find('.block_images img').eq(index).addClass('imgLoaded');
        };

        scope.blockImagesReadyCheck = function() {
          var numPhotos = scope.block.photos.length;

          // if no photos, we don't need to check for photos being loaded.
          if (!numPhotos) {
            return true;
          }

          // if not all img elements are added to the DOM yet, obviously return false.
          if ($(elm).find('.block_images img').length !== numPhotos) {
            return false;
          }

          if ($(elm).find('.block_images .imgLoaded').length === numPhotos) {
            return true;
          }

          return false;
        };

        scope.blockImagesReady = function() {
          $(elm).find('.block_images').removeClass('blockImagesNotReady');
          $(elm).find('.block_images').addClass('blockImagesReady');

          // make photos sortable.
          $photosContainer.find('.block_images').sortable({
            handle: '[data-js="photo-reorder"], img, div.grid_image',
            helper: 'clone',
            containment: 'parent',
            zIndex: 9,
            tolerance: 'pointer',
            //appendTo: $photosContainer, // not working, so do it manually in the start function.
            start: function(e, ui) {
              ui.item.appendTo('body');
              ui.item.css('display', 'none');
            },
            stop: function(e, ui) {
              var $images = $(elm).find('div.image-wrapper');
              for (var i = 0; i < $images.length; i++) {
                var photoScope = angular.element($images.eq(i).get(0)).scope();
                photoScope.photo.order = i;
              }
              scope.$root.$broadcast('block-contents-changed');
            }
          });

          // when images loaded, emit an event so the loading sign can be removed.
          scope.$root.$broadcast('blockLoaded');
        };
        // }}}

        /*
         * Events
         */
        $caption.on('blur', function() {
          scope.$root.$broadcast('block-contents-changed');
        });

        scope.$on('photos-updated', function() {
          scope.part = null;
        });

        /*
         * Watches
         */
        scope.$watch('block.grid_type', function(newValue, oldValue) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
            scope.updateAlignment(newValue);
          }
        });

        scope.$watch('block.grid_size', function(newValue, oldValue) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
            scope.$broadcast('photos-updated');
          }
        });

        scope.$watch('block.alignment', function(newValue, oldValue) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
          }
        });

        /*
         * Initial Logic
         */
        scope.updateAlignment(scope.block.grid_type);

        // put photos in order.
        for (var i=0; i<scope.block.photos.length; i+=1) {
          photo = scope.block.photos[i];
          if (typeof photo.order != "undefined") {
            newPhotoArray[photo.order] = photo;
          }
          else { break; }
        }

        // if the user has rearranged photos at any given time.
        if (newPhotoArray.length > 0) {
          scope.block.photos = newPhotoArray;
        }

        // if no photos, just say the block is loaded, otherwise the
        // blockLoaded event will be emitted after all images are loaded.
        if (!scope.block.photos.length) {
          scope.$root.$broadcast('blockLoaded');
        }

      }
    };
  }]);

  // The equalHeightCaptions attribute directive accepts an array of CSS
  // selectors, and must be on or inside of a block directive. The elements matched for each selector (captions) are assumed
  // to contain text with a uniform font size and line height. The elements
  // matching a selector will be made the same height.
  //
  // This probably doesn't have to be a separate directive.
  app.directive('equalHeightCaptions', ['$timeout', '$interpolate', function($timeout, $interpolate) {
    return {
      restrict: 'A',

      link: function($scope, $element, $attributes) {
        var selectors = $scope.$eval($attributes.equalHeightCaptions);
        var numberOfCaptionsVisible = 0;
        var captionsPerImage = selectors.length;
        var grid_size = $scope.block.grid_size;

        $scope.updateCaptions = function() {
          numberOfCaptionsVisible += 1;

          // if all captions are visible.
          if (
            numberOfCaptionsVisible % (captionsPerImage * $scope.block.photos.length) === 0 &&
              $scope.block.grid_type == 'grid'
          ) {
            _.each(selectors, function(selector, index) {
              var captions = $element.find(selector);
              var mostLines = 0;
              var lineHeight = parseInt(captions.css('line-height'));
              var numberOfRows = Math.ceil(captions.length/grid_size);
              var caption;
              var numberOfLines;

              for (var row=0; row<numberOfRows; row+=1) {
                mostLines = 0;

                var column;

                for (column = 0; column<grid_size; column+=1) {
                  caption = captions.eq(column+row*grid_size);

                  if (caption.length) {
                    numberOfLines = caption.height()/lineHeight;

                    if (numberOfLines > mostLines) {
                      mostLines = numberOfLines;
                    }
                  }
                }

                for (column = 0; column<grid_size; column+=1) {
                  caption = captions.eq(column+row*grid_size);

                  if (caption.length) {
                    caption.parent().height(lineHeight*mostLines);
                  }
                }
              }
            }); // _.each
          } // if
        }; // $scope.updateCaptions
      } // link
    };
  }]);

})(window);
