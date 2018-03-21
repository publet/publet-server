(function($) {

  var updateSentCount = 0;
  var updateInterval;

  $(function() {

    var iframeMessageEvent = null;

    function onMessageReceived(e) {
      iframeMessageEvent = e;
      sendHeightUpdate();

      updateInterval = setInterval(function() {
        sendHeightUpdate();
      }, 500);

    }

    function sendHeightUpdate() {
      if (!iframeMessageEvent) {
        return;
      }

      if (updateSentCount > 10) {
        clearInterval(updateInterval);
      }

      var message = {
        height: $(document).height(),
        id: window.id,
        name: 'embed'
      };

      iframeMessageEvent.source.postMessage(message, iframeMessageEvent.origin);
      updateSentCount++;
    }

    if (window.addEventListener){
      window.addEventListener('message', onMessageReceived, false);
    } else {
      window.attachEvent('onmessage', onMessageReceived, false);
    }

  });

}(jQuery));
