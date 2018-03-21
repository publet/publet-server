(function(window) {

  var app = window.app;
  var angular = window.angular;
  var _ = window._;

  app.factory('api', ['$http', function($http) {
    var argnames = ['url', 'headers', 'group', 'no_authorization', 'data'];
    var argset = _.object(argnames, argnames);
    function api(method, args) {
      var httpArgs = {
        url: args.url,
        method: method,
        headers: angular.copy(args.headers || {})
      };
      if (httpArgs.url === undefined) {
        throw new TypeError('api() missing required argument url');
      }
      _.each(args, function (v, k) {
        if (argset[k] === undefined) {
          throw new TypeError('api() received unexpected argument "' + k + '"');
        }
      });
      if (args.data) {
        httpArgs.data = args.data;
      }
      if (args.group && window.group_id) {
        httpArgs.headers.group = window.group_id;
      }
      if (!args.no_authorization) {
        httpArgs.headers.Authorization = 'ApiKey ' + window.user + ':' + window.user_api_key;
      }
      return $http(httpArgs); // returns a $q promise.
    }
    _.each(['POST', 'GET', 'DELETE', 'PUT'], function (method) {
      api[method] = function (args) {
        return api(method, args); // returns a $q promise.
      };
    });
    return api;
  }]);
})(window);
