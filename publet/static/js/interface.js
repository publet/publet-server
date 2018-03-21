(function($) {

  var app = window.app;

  app.controller('RegistrationController', ['$scope', function($scope) {}]);

  $(function() {

    /*
     * Keep track of scrolling to make the tool menu stay at the top of the window.
     */
    var currentScrollPosition;
    var previousScrollPosition = 0;

    var offsetTools = $('.article__tools').offset();
    var toolsPos = offsetTools ? offsetTools.top : 0;
    var offsetSidebar = $('.article__sidebar').offset();
    var sidebarPos = offsetSidebar ? offsetSidebar.top : 0;

    var $tools = $('.article__header');
    var dummyTools = $('<div></div>');
    dummyTools.css({'width':'100%'});

    $(window).scroll(function(event) {
      currentScrollPosition = event.currentTarget.scrollY; // TODO: cross browser?

      if (currentScrollPosition > sidebarPos && previousScrollPosition <= sidebarPos) {
        $('.article__sidebar').addClass('fixed');
      }
      else if (currentScrollPosition <= sidebarPos && previousScrollPosition > sidebarPos) {
        $('.article__sidebar').removeClass('fixed');
      }

      if (currentScrollPosition > toolsPos && previousScrollPosition <= toolsPos) {
        dummyTools.height($tools.height());
        $tools.addClass('fixed');
        $tools.after(dummyTools);
      }
      else if (currentScrollPosition <= toolsPos && previousScrollPosition > toolsPos) {
        $tools.removeClass('fixed');
        dummyTools.detach();
      }

      previousScrollPosition = currentScrollPosition;
    });

    // Dropdown menus
    // NOTE: This is the old nav
    /* $('.dropdown__trigger').click(function() {
       $(this).parent('.dropdown').toggleClass('-active');
       });

       $('html').click(function() {
       $('.dropdown').removeClass('-active');
       });

       $('.dropdown').click(function(e) {
       e.stopPropagation();
       });

       //toggle menu
       $(document.body).on( 'click', 'li.button-edit-block a', function() {
       $(this).parents('.text-block').find('div.dropdown__menu').css('display','none');
       $(this).parents('.text-block').find('a.dropdown__trigger').removeClass('active');
       });

       $(document.body).on( 'click', 'a.dropdown__trigger', function() {
       $(this).parent().find('div.dropdown__menu').toggle();
       $(this).toggleClass('active');
       }); */

    // Block interface dropdown menus

    //select options
    $(document.body).on( 'click', 'div.dropdown-attribute', function() {
      $(this).find('input').click();
    });

    /*
     * Block Focus and Blcok Control visibility
     */
    // TODO: Move this off of window and into the appropriate scope.
    window.focusCtrl = new FocusController(); // see interface-modules.js, needs to be global, other files use it (until a module system is in place).
    focusCtrl.initialize();

    // TODO: Move this off of window and into the appropriate scope.
    window.showBlockControls = function($targetBlock) {
      $targetBlock = $($targetBlock);
      $targetBlock.find('.block-controls').stop();
      $targetBlock.find('.block-controls').fadeIn({duration: 500, easing: 'easeOutExpo'});
    };

    // TODO: Move this off of window and into the appropriate scope.
    window.hideBlockControls = function($targetBlock) {
      $targetBlock = $($targetBlock);
      $targetBlock.find('.block-controls').stop();
      $targetBlock.find('.block-controls').fadeOut({duration: 500, easing: 'easeOutExpo'});
    };

    $('.article__main').on( 'mouseenter', 'div.block', function() {
      window.showBlockControls($(this));
      if (!$('div.current').length) {
        focusCtrl.setSelectedNodes($(this).get());
      }
    });

    $('.article__main').on( 'mouseleave', 'div.block', function() {
      if (!$(this).is('.current')) {
        window.hideBlockControls($(this));
      }
      if (!$('div.current').length) {
        focusCtrl.clearSelectedNodes();
      }
    });

    $(document).on('mouseleave', '#insertion-line', function(event) {
      hideInsertionStuff();
    });

    function showInsertionStuff() {
      var $insertionLine = $('#insertion-line');
      var $insertionSymbol = $('#insertion-symbol');
      var $insertionCanvas = $('#insertion-canvas');
      $insertionLine.show();
      //$insertionSymbol.show();
      //$insertionCanvas.show();
    }
    function hideInsertionStuff() {
      var $insertionLine = $('#insertion-line');
      var $insertionSymbol = $('#insertion-symbol');
      var $insertionCanvas = $('#insertion-canvas');
      $insertionLine.hide();
      $insertionSymbol.hide();
      $insertionCanvas.hide();
    }

    /*
     * Color control field
     */
    $(document.body).on( 'focus', 'input#add-color-field', function() {
      $(this).parent('span').addClass('focused');
    });
    $(document.body).on( 'blur', 'input#add-color-field', function() {
      $(this).parent('span').removeClass('focused');
    });

    $('.added').timeago();

  });

  app.controller('SearchController', ['$scope', '$http', '$sce', function($scope, $http, $sce) {
    $scope.trust = function(html) {
      return $sce.trustAsHtml(html);
    };

    $scope.runSearch = function() {
      $http({
        url: '/api/group/' + window.PB.group_id + '/hub/' + window.PB.hub_id + '/search/',
        method: 'GET',
        params: {
          query: $scope.keywords
        }
      }).then(function(results) {
        $scope.results = results.data;
      });
    };
  }]);

  app.controller('FeedbackController', ['$scope', '$timeout', 'FeedbackStorage', function($scope, $timeout, FeedbackStorage) {
    $scope.button = 'Send';

    $scope.submit = function() {
      $scope.button = 'Sending...';

      FeedbackStorage.send($scope.text, window.location.href).then(function() {
        $scope.text = '';
        $scope.button = 'Sent!';

        $timeout(function() {
          $scope.button = 'Send';
        }, 2000);

      });
    };
  }]);

})(jQuery);
