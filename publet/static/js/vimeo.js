(function() {

  var Vimeo = (function() {

    function Vimeo() {
      var self = this;
      this.videos = {};
      this.callbacks = {};

      window.EventBus.register('vimeo', onMessageReceived);

      function onMessageReceived(data) {
        if (data.event === 'ready' && self.videos[data.player_id]) {
          self.videos[data.player_id].ready = true;
        }

        var method = data.event || data.method;

        if (self.callbacks[data.player_id]) {
          var callback = self.callbacks[data.player_id][method];

          if (callback) {
            callback(data);
          }
        }

      }
    }

    Vimeo.prototype.register = function(id, $el, callback) {
      this.videos[id] = {
        ready: false,
        el: $el,
        url: 'https://player.vimeo.com/video/' + id
      };

      this.callbacks[id] = {
        ready: callback
      };
    };

    Vimeo.prototype.play = function(id) {
      if (this.videos[id].ready) {
        return this.post(id, 'play');
      }
    };

    Vimeo.prototype.getVideoSize = function(id, callback) {
      var self = this;

      this.post(id, 'getVideoHeight', function(heightObj) {
        self.post(id, 'getVideoWidth', function(widthObj) {
          callback({
            width: widthObj.value,
            height: heightObj.value
          });
        });
      });
    };

    Vimeo.prototype.post = function(id, action, callback) {

      if (callback) {
        if (!this.callbacks[id]) {
          this.callbacks[id] = {};
        }
        this.callbacks[id][action] = callback;
      }

      var video = this.videos[id];
      var data = {
        method: action
      };

      video.el[0].contentWindow.postMessage(JSON.stringify(data), video.url);
    };

    return Vimeo;

  })();

  window.VIMEO = new Vimeo();


}).call(this);
