(function($) {
  // Event bus mechanism for handling iframe messages

  var EventBus = (function() {
    var self;

    function EventBus() {
      this.callbacks = {};
      self = this;

      if (window.addEventListener){
        window.addEventListener('message', onMessageReceived, false);
      } else {
        window.attachEvent('onmessage', onMessageReceived, false);
      }
    }

    function isVimeoEvent(e) {
      if (e.origin.indexOf('vimeo') > -1) {
        return true;
      }
    }

    function onMessageReceived(e) {
      var data;

      if (typeof e.data === 'string') {
        data = JSON.parse(e.data);
      }

      if (!data) {
        data = e.data;
      }

      var callback;

      if (isVimeoEvent(e)) {
        callback = self.callbacks.vimeo;
      } else {
        callback = self.callbacks[data.name];
      }

      if (callback) {
        callback(data, e);
      }

    }

    // Register a message listener
    EventBus.prototype.register = function(name, callback) {
      this.callbacks[name] = callback;
    };

    return EventBus;

  })();

  window.EventBus = new EventBus();

})(jQuery);
