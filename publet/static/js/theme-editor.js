(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  app.controller('ThemeEditorController',
                 ['$scope', '$timeout', 'ThemeStorage', 'FontStorage',
                   'FlavorStorage', 'ColorStorage',
                  function($scope, $timeout, ThemeStorage, FontStorage,
                           FlavorStorage, ColorStorage) {
    $scope.theme = window.theme;
    $scope.saveButton = 'Save';
    $scope.newFontFiles = [];
    $scope.static = window.static;

    $scope.alignmentChoices = app.alignmentChoices;
    $scope.textAlignmentChoices = app.textAlignmentChoices;
    $scope.sizes = app.sizes;
    $scope.fontStyles = app.fontStyles;
    $scope.line_heights = app.line_heights;

    $scope.formatColorCell = app.formatColorCell;
    $scope.escapeMarkup = app.escapeMarkup;
    $scope.select2Options = app.select2Options;

    // Colors

    $scope.addColor = function() {
      $scope.theme.colors.push({
        hex: $scope.newColor
      });
      $scope.newColor = '';
    };

    $scope.getColorByUri = function(uri) {
      var res;
      $.each($scope.theme.colors, function(index, item) {
        if (item.resource_uri === uri) {
          res = item.hex;
          return;
        }
      });
      return res;
    };

    $scope.removeColor = function(id) {
      if (!confirm('Are you sure?')) {
        return;
      }

      var colorIndex;

      $.each($scope.theme.colors, function(index, item) {
        if (item.id == id) {
          colorIndex = index;
          return false;
        }
      });

      ColorStorage.removeColor(id).then(function() {
        $scope.theme.colors.splice(colorIndex, 1);
      });

    };

    // Fonts

    $scope.addFont = function() {
      FontStorage.addFont({
        name: $scope.fontName,
        family: $scope.font_family,
        files: $.map($scope.newFontFiles, function(e) {
          return {
            'file': e.url,
            'filename': e.filename,
            'style': e.style
          };
        })
      }).then(function(response) {
        $scope.theme.fonts.push(response.data);

        // Clear it out
        $scope.fontName = '';
        $scope.font_family = '';
        $scope.newFontFiles = [];
      });
    };

    $scope.removeFont = function(id) {
      var fontIndex;
      $.each($scope.theme.fonts, function(index, item) {
        if (item.id == id) {
          fontIndex = index;
          return false;
        }
      });
      $scope.theme.fonts.splice(fontIndex, 1);
    };

    $scope.chooseFontFile = function() {
      var settings = angular.copy(window.FP.write);
      settings.multiple = true;
      filepicker.pickAndStore(settings, {}, function(fpfiles) {
        $.each(fpfiles, function(i, el) {
          $scope.newFontFiles.push(el);
        });
        $scope.$apply();
      });
    };

    // Other

    $scope.save = function() {
      $scope.saveButton = 'Saving...';
      ThemeStorage.saveTheme($scope.theme).then(function(r) {
        $scope.saveButton = 'Saved!';
        $timeout(function() {
          $scope.saveButton = 'Save';
        }, 1000);
      });
    };

    // Flavors

    $scope.addFlavor = function(type) {
      var field = type + '_flavor_name';
      var name = $scope[field] || 'New flavor';

      FlavorStorage.addFlavor({
        type: type,
        theme: $scope.theme.resource_uri,
        name: name
      }).then(function(response) {
        $scope.theme.flavors.push(response.data);
        $scope[field] = '';
      });
    };

    $scope.removeFlavor = function(id) {
      var flavorIndex;

      $.each($scope.theme.flavors, function(index, item) {
        if (item.id == id) {
          flavorIndex = index;
          return false;
        }
      });

      FlavorStorage.removeFlavor(id).then(function() {
        $scope.theme.flavors.splice(flavorIndex, 1);
      });
    };

  }]);

  app.controller('ThemeListController', ['$scope', '$timeout', 'ThemeStorage', function($scope, $timeout, ThemeStorage) {
    $scope.addTheme = function() {
      ThemeStorage.addTheme($scope.newThemeName, window.group_pk).then(function(r) {
        if (r.status === 201) {
          window.location.href = '/groups/' + window.group_slug +
            '/themes/' + r.data.slug + '/';
        }
      });
    };
  }]);

})(window);
