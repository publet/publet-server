(function(window) {

  // Get the app.
  var app = window.app;

  // English shortened
  jQuery.timeago.settings.strings = {
    prefixAgo: null,
    prefixFromNow: null,
    suffixAgo: "ago",
    suffixFromNow: "",
    seconds: "1m",
    minute: "1m",
    minutes: "%dm",
    hour: "1h",
    hours: "%dh",
    day: "1d",
    days: "%dd",
    month: "1mo",
    months: "%dmo",
    year: "1yr",
    years: "%dyr",
    wordSeparator: " ",
    numbers: []
  };

  // Filters.
  app.filter('timeago', function() {
    return function(time) {
      if (!time) {
        return;
      }
      time = time + 'Z';
      return $.timeago(time);
    };
  });

  // Services.
  app.factory('SaveService', ['$rootScope', '$timeout', '$q', function($rootScope, $timeout, $q) {
    return {
      save: function(form, saveFn, saveObj) {

        if ((form && form.$invalid) || $rootScope.savingDisabled) {
          return $q.reject();
        }
        
        $rootScope.savingDisabled = true;
        $rootScope.saveStatus = 'Saving...';
        $rootScope.saveNowText = 'Saving...';
        $rootScope.articleLastModified = '';

        if (!$rootScope.$$phase) {
          $rootScope.$apply();
        }

        // FIXME: The following returns a promise if--and only if-- saveFn is
        // promised. This can lead to accidental breaking of promise chains
        // which can be time consuming to hunt down.
        var promise = saveFn(saveObj);
        return promise.then(function(response) {

          $rootScope.savingDisabled = false;
          $rootScope.saveStatus = '';
          $rootScope.saveNowText = 'Save now';
          $rootScope.articleLastModified = response.data.modified;

          return response;
        });
      }
    };
  }]);

})(window);
