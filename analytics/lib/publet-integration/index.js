var integration = require('analytics.js-integration');

var Publet = module.exports = integration('Publet')
  .global('_publet');

Publet.prototype.loaded = function(){
  return !! (window._publet && window._publet.push != [].push);
};

Publet.prototype.track = function (event) {
  window._publet.push(['track', event]);
};

Publet.prototype.page = function (page) {
  window._publet.push(['page', page]);
};

Publet.prototype.identify = function (identify) {
  window._publet.push(['identify', identify]);
};

Publet.prototype.initialize = function() {
  this._ready = true;
  window._publet = window._publet || [];
};
