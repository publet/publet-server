(function($) {
  'use strict';

  function choose(e) {
    var href = e.target.href;
    var pub = href.split('/').reverse()[0];

    var msg = {
      action: 'choosePublication',
      publication: pub
    };

    chrome.runtime.sendMessage(msg, function(response) {
      if (response.error) {
        $('#publications').html('<p>Please log in to Publet in your browser first.</p>');
      } else {
        $('#publications').html('<h3>Saved!</h3>');
        setTimeout(function() {
          window.close();
        }, 1000);
      }
    });

    return false;
  }

  function renderPubs(html) {
    $('#publications').html(html);
  }

  function getPublications(callback) {
    chrome.runtime.sendMessage({action: 'getPublications'}, function(response) {
      if (!response.success) {
        $('#publications').html('<p>Please log in to Publet in your browser first.</p>');
      } else {
        callback(response.html);
      }
    });
  }

  $(function() {
    $('a').live('click', choose);
    getPublications(renderPubs);

  });

})(jQuery);
