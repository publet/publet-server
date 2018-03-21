(function($) {

  var root = window.self;

  // The window is a view of the document that is the browser window.  This
  // function gets the position of the window in the document.  It returns an
  // object that says where the top and the bottom edge of the window are.
  function getVisibleViewport() {
    var $w = $(window);
    return {
      top: $w.scrollTop(),
      bottom: $w.scrollTop() + $w.height()
    };
  }

  // Given a visible viewport, return a filter function.  This function
  // determines whether an element is currently visible.
  function isInView(visible) {
    return function(i, el) {
      if (
        // the top edge of the element is in view
        ((el.top > visible.top) && (el.top < visible.bottom)) ||
          // or the bottom edge of the element is in view
          ((el.bottom > visible.top) && (el.bottom < visible.bottom)) ||
          // or the top edge is above the viewport and the bottom edge is below
          // the viewport
          ((el.top < visible.top) && (el.bottom > visible.bottom))
      ) {
        return true;
      } else {
        return false;
      }
    };
  }

  function getVisibleArticles() {
    var $articles = $('.article-container');
    var articlePositions = $articles.map(function(i, el) {
      var $el = $(el).find('.container');
      return {
        top: $el.offset().top,
        bottom: $el.offset().top + $el.height(),
        id: parseInt(el.id.split('-')[1], 10)
      };
    });

    var visible = getVisibleViewport();
    return articlePositions.filter(isInView(visible));
  }

  function getVisibleBlocks() {
    var $blocks = $('div[block]');

    var blockPositions = $blocks.map(function(i, el) {
      var $el = $(el);
      return {
        top: $el.offset().top,
        bottom: $el.offset().top + $el.height(),
        id: parseInt(el.id.split('-')[1], 10)
      };
    });

    var visible = getVisibleViewport();
    return blockPositions.filter(isInView(visible));

  }

  root.getVisibleViewport = getVisibleViewport;
  root.isInView = isInView;
  root.getVisibleArticles = getVisibleArticles;
  root.getVisibleBlocks = getVisibleBlocks;

  return root;

}(jQuery));
