(function($) {
  'use strict';

  var baseUrl = 'https://beta.publet.com';

  function getPublications(callback) {
    $.ajax({
      url: baseUrl + '/api/chrome-extension',
      success: function(data) {
        callback({
          success: true,
          html: data
        });
      },
      error: function() {
        callback({
          success: false
        });
      }
    });
  }

  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {

    // sending message to popup
    if (request.action === 'getPublications') {
      getPublications(function(response) {
        sendResponse(response);
      });
      return true;  // super important
    }

    // sending message to content
    if (request.action === 'choosePublication') {
      chrome.tabs.getSelected(null, function(tab) {
        chrome.tabs.sendMessage(tab.id, {}, function(resp) {
          $.ajax({
            url: baseUrl + '/api/readability/' + request.publication,
            type: 'post',
            data: {
              url: resp.url
            },
            success: function(data) {
              sendResponse({});
            },
            error: function() {
              sendResponse({
                error: true
              });
            }
          });
        });
      });

      return true;
    }

  });

})(jQuery);
