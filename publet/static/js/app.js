(function() {

  // Be specific as to what 'this' is, here.
  var window = this;

  // Forward declaration of the template module
  angular.module('templates', []);

  // Core app.
  var app = angular.module('Publet', ['angular-flexslider', 'templates',
                           'ui.select2', 'ngAnimate', 'highcharts-ng']);

  // Use non-Django-style interpolation.
  app.config(['$interpolateProvider', '$locationProvider', '$sceDelegateProvider', function($interpolateProvider, $locationProvider, $sceDelegateProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');

    $sceDelegateProvider.resourceUrlWhitelist([
      'self',
      'http*://www.youtube.com/**',
      'http*://youtube.com/**',
      'http*://youtu.be/**',
      'http*://vimeo.com/**',
      'http*://player.vimeo.com/**',
      'https://w.soundcloud.com/**'
    ]);
  }]);

  app.textAlignmentChoices = [
    {id: 'l', name: 'Left'},
    {id: 'r', name: 'Right'},
    {id: 'c', name: 'Center'}
  ];

  app.alignmentChoices = [
    {id: '0', name: 'Column'},
    {id: '1', name: 'Full'},
    {id: '2', name: 'Breaking'},
    {id: '3', name: 'Breaking left'},
    {id: '4', name: 'Breaking right'},
    {id: '5', name: 'Margin left'},
    {id: '6', name: 'Margin right'},
    {id: '7', name: 'Column left'},
    {id: '8', name: 'Column right'}
  ];

  app.photoSizeChoices = [
    {id: 's', name: 'Small'},
    {id: 'm', name: 'Medium'},
    {id: 'l', name: 'Large'}
  ];

  app.alignmentClasses = {};

  _.each(app.alignmentChoices, function(el) {
    app.alignmentClasses[el.id] = 'align-' + el.name.toLowerCase().replace(' ', '-');
  });

  app.sizes = [
    8, 10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 48, 56, 64, 72, 80, 88, 96, 104
  ];

  app.line_heights = [
    '1', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '1.9', '2',
    '2.5', '3'
  ];

  app.fontStyles = ['normal', 'italic', 'bold', 'italic-bold'];

  app.formatColorCell = function(state) {
    var h = state.text;
    return '<span style="background-color: #' + h +
      '; display: inline-block; width: 10px; height: 10px; margin-right: 5px"></span>' + h;
  };

  app.select2Options = {
    dropdownAutoWidth: true
  };

  app.escapeMarkup = function(m) {
    return m;
  };

  app.changeHandler = function(newValue, oldValue, scope) {
    if (newValue !== oldValue) {
      scope.$root.$broadcast('block-contents-changed');
    }
  };

  app.now = Date.now || function() { return new Date().getTime(); };

  app.filter('currency', function() {
    return function(pennies) {
      if (pennies === undefined) {
        return '';
      }

      pennies = pennies / 100;
      // http://stackoverflow.com/a/14428340/244182
      return pennies.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
    };
  });

  // Export the app.
  window.app = app;

}).call(this);
