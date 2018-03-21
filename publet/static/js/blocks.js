(function(window, _) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  // Directives.
  app.directive('block', [function() {
    // Note: The scope of this directive is shared with the more specific block
    // directives (photoBlock, textBlock, etc) via the controller of this directive.
    return {
      restrict: 'A',
      controller: ['$scope', function($scope) { // empty. Just creates a shared scope between this directive and photoBlock, textBlock, etc.
        $scope.$blockScope = $scope;
        $scope.isEmpty = function() {
          // Implemented by each sub-type of block (photo, audio, text, video, etc).
        };
      }],
      link: function postLink(scope, elm, attrs) {

        var $block = $(elm).closest('.block'),
          $toggle = $(elm).find('.toggleButton'),
          $ctaLink = $(elm).find('.cta_link'),
          $ctaLabel = $(elm).find('.cta_label'),
          $meta = $(elm).find('.meta'),
          $customCss = $(elm).find('.custom_css');

        scope.active = false;
        scope.sizes = app.sizes;
        scope.line_heights = app.line_heights;
        scope.canEdit = window.canEdit;

        scope.defaultPlaceholders = {
          'alignment': 'Position',
          'font': 'Font',
          'size': 'Size',
          'text_alignment': 'Justification',
          'color': 'Color',
          'line_height': 'Line spacing',
          'grid_type': 'Single image',
          'grid_size': 3
        };

        scope.lock = function(block) {
          block.is_locked = true;
          scope.$root.$broadcast('block-contents-changed');
        };

        scope.unlock = function(block) {
          block.is_locked = false;
          scope.$root.$broadcast('block-contents-changed');
        };

        scope.showSubmitToIntegration = function() {
          scope.$parent.selectingIntegration = true;
          scope.$parent.integrationBlock = scope.block;
        };

        scope.getCurrentFlavorObject = function() {
          if (!scope.block.flavor) {
            return null;
          }

          var flavors = scope.$parent.allFlavors;
          var id = parseInt(scope.block.flavor.split('/')[3], 10);

          return _.find(flavors, function(el) {
            return el.id === id;
          });

        };

        scope.updateFlavorPlaceholders = function() {

          if (!scope.flavorObject) {
            scope.placeholders = scope.defaultPlaceholders;
            return true;
          }

          var fields = ['alignment', 'font', 'size', 'text_alignment',
            'color', 'line_height'];

          var color;
          var font;

          if (scope.flavorObject.color && scope.flavorObject.color.hex) {
            color = scope.flavorObject.color.hex;
          }

          if (scope.flavorObject.font && scope.flavorObject.font.name) {
            font = scope.flavorObject.font.name;
          }

          scope.placeholders = {
            'color': color || scope.defaultPlaceholders.color,
            'font': font || scope.defaultPlaceholders.font,
            'alignment': scope.flavorObject.display.alignment || scope.defaultPlaceholders.alignment,
            'text_alignment': scope.flavorObject.display.text_alignment || scope.defaultPlaceholders.text_alignment,
            'size': scope.flavorObject.size || scope.defaultPlaceholders.size,
            'line_height': scope.flavorObject.line_height || scope.defaultPlaceholders.line_height
          };

        };

        scope.removeIfEmpty = function() {
          if (scope.isEmpty()) { // isEmpty is implemented for each type of block. Look in each {photo,text,video,audio,etc}-block.js.
            scope.deleteState.blockToBeDeleted = scope.block;
            scope._removeBlock();
          }
        };

        scope.choosePhoto = function(field) {
          filepicker.pickAndStore(window.FP.write, {}, function(fpfiles) {
            var blob = fpfiles[0];
            var url = blob.url;

            var options = $.extend(true, {}, window.FP.write);
            options.width = true;
            options.height = true;

            filepicker.stat(blob, options, function(metadata) {
              scope.block[field] = url;

              scope.block.width = metadata.width;
              scope.block.height = metadata.height;

              scope.$root.$broadcast('block-contents-changed');
              scope.$apply();
            });
          });
        };

        scope.clearFlavorValues = function() {
          scope.placeholders = scope.defaultPlaceholders;
          scope.block.alignment = '';
          scope.block.font = null;
          scope.block.size = null;
          scope.block.text_alignment = '';
          scope.block.color = null;
          scope.block.line_height = null;
        };

        scope.blur = function() {
          scope.$root.$broadcast('block-contents-changed');
        };

        scope.toggling = false;
        scope.toggleBlock = function() {
          scope.toggling = true;
          scope.$root.$broadcast('close-all-blocks');
          if (scope.active) {
            scope.active = false;
          }
          else {
            scope.active = true;
          }
          scope.toggling = false;
        };

        scope.showBlockControlsIfNew = function() {
          if (scope.block.isNew) {
            scope.toggleBlock();
            window.showBlockControls(elm);
          }
        };

        scope.hasBlockControls = function() {
          return $(elm).find('.block-controls').length > 0? true: false;
        };

        scope.blockControlsReady = function() {
          // use this if you want to detect when block
          // control templates have been loaded
        };

        scope.$root.$on('close-all-blocks', function() {
          if (!scope.toggling) {
            scope.active = false;
          }
        });

        scope.$watch('active', function(newValue, oldValue) {
          // TODO: Don't touch the DOM in a $watch
          if (newValue !== oldValue) {
            if (!$toggle.length) {
              $toggle = $(elm).find('.toggleButton');
            }

            if (scope.active) {
              window.focusCtrl.setSelectedNodes($(elm).closest('.block').get());
              $block.addClass('current');
              $toggle.addClass('eye_open');
              $toggle.removeClass('pencil');
            }
            else if(!scope.active) {
              $block.removeClass('current');
              $toggle.removeClass('eye_open');
              $toggle.addClass('pencil');
              //window.hideBlockControls(elm);
              scope.removeIfEmpty();
            }
          }
        });

        scope.$watch('block.' + scope.field, function(newValue, oldValue) {
          if (newValue !== oldValue) {
            var get = '?signature=' + window.FP.read.signature +
              '&policy=' + window.FP.read.policy;
            scope.block.image_url = newValue + get;
          }
        });

        scope.$watch('block.custom_css_classes', app.changeHandler);
        scope.$watch('block.has_metadata', app.changeHandler);
        scope.$watch('block.has_cta', app.changeHandler);
        scope.$watch('block.cta_alignment', app.changeHandler);
        scope.$watch('block.font', app.changeHandler);
        scope.$watch('block.color', app.changeHandler);
        scope.$watch('block.shareable', app.changeHandler);
        scope.$watch('block.full_size', app.changeHandler);
        scope.$watch('block.flavor', function(newValue, oldValue, scope) {
          if (newValue !== oldValue) {
            scope.clearFlavorValues();
            scope.flavorObject = scope.getCurrentFlavorObject();
            scope.updateFlavorPlaceholders();
            scope.$root.$broadcast('block-contents-changed');
          }
        });

        $ctaLink.on('blur', function() {
          scope.$root.$broadcast('block-contents-changed');
        });

        $ctaLabel.on('blur', function() {
          scope.$root.$broadcast('block-contents-changed');
        });

        $meta.on('blur', function() {
          scope.$root.$broadcast('block-contents-changed');
        });

        $customCss.on('blur', function() {
          scope.$root.$broadcast('block-contents-changed');
        });

        scope.flavorObject = scope.getCurrentFlavorObject();
        scope.updateFlavorPlaceholders();

        if (scope.block.alignment === '') {
          scope.block.alignment = null;
        }

        if (scope.block.text_alignment === '') {
          scope.block.text_alignment = null;
        }

        scope.chooseFile = scope.choosePhoto;
        scope.alignmentChoices = app.alignmentChoices;
        scope.textAlignmentChoices = app.textAlignmentChoices;
        scope.photoSizeChoices = app.photoSizeChoices;

      }
    };

  }]);

  // TODO: This was done before angular had ng-blur; conver to standard API
  app.directive('ngBlurPublet', ['$parse', function($parse) {
    return function(scope, element, attr) {
      var fn = $parse(attr.ngBlurPublet);
      element.bind('blur', function(event) {
        scope.$apply(function() {
          fn(scope, {$event:event});
        });
      });
    };
  }]);

  app.directive('mediumEditor', [function() {

    return {
      require: 'ngModel',
      restrict: 'AE',
      link: function(scope, elem, attrs, ctrl) {

        var editor = new MediumEditor(elem, {
          placeholder: '',
          buttons: ['bold', 'italic', 'underline', 'anchor',
            'quote', 'unorderedlist', 'orderedlist',
            'superscript', 'subscript', 'strikethrough', 'pre'],
          checkLinkFormat: true
        });

        var updateContent = function(e) {
          scope.block.content = elem.html();

          scope.$apply(function() {
            ctrl.$setViewValue(elem.html());
          });
        };

        elem.on('input', updateContent);
        elem.on('blur', updateContent);

        ctrl.$render = function() {
          elem.html(ctrl.$isEmpty(ctrl.$viewValue) ? '' : ctrl.$viewValue);
        };

        // The watcher is updated each time the content of the contenteditable
        // are updated so we debounce the function to slow down saving to at
        // most once per 1.5 seconds.
        scope.$watch('block.content', _.debounce(function(newValue, oldValue, scope) {
          if (newValue !== oldValue) {
            scope.$root.$broadcast('block-contents-changed');
          }
        }, 1500));

      }
    };
  }]);

  app.directive('crop', ['$parse', function($parse) {
    return {
      restrict: 'A',
      link: function(scope, elm, attrs) {
        var fn = $parse(attrs.crop);
        var model = fn(scope);

        var $img = $(elm).find('.image');
        var jCropInstance, options;

        options = {
          onSelect: function(c) {
            var tracker = $img.parent().children('.jcrop-tracker');
            model.crop_marks = {
              x: c.x,
              y: c.y,
              x2: c.x2,
              y2: c.y2,
              width: tracker.width(),
              height: tracker.height()
            };

            scope.$root.$broadcast('block-contents-changed');
          }
        };

        // Initial crop text

        if (model.crop_marks) {
          scope.cropText = 'Edit crop';
        } else {
          scope.cropText = 'Crop image';
        }

        scope.crop = function() {
          scope.isCropping = true;

          if (!jCropInstance) {
            jCropInstance = $.Jcrop($img);
          }

          if (model.crop_marks) {
            jCropInstance.enable();
            jCropInstance.setSelect([
              model.crop_marks.x,
              model.crop_marks.y,
              model.crop_marks.x2,
              model.crop_marks.y2
            ]);

            jCropInstance.setOptions(options);

          } else {

            jCropInstance.enable();
            jCropInstance.setOptions(options);
          }
        };

        scope.cancelCrop = function() {
          jCropInstance.release();
          jCropInstance.disable();
        };

      }
    };
  }]);

})(window, _);
