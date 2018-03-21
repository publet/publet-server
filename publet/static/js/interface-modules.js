(function(window) {

  /*!
   * FocusController is based on Fokus 0.5 by Hakim.
   *
   * Fokus 0.5
   * http://lab.hakim.se/fokus
   * MIT licensed
   * Copyright (C) 2012 Hakim El Hattab, http://hakim.se
   */
  var FocusController = (function() {
    function FocusController() {

      // Padding around the selection
      this.PADDING = 0;

      // Opacity of the overlay
      this.OPACITY = 0.1;

      // Key modifier that needs to be held down for overlay to appear
      this.MODIFIER = null;

      // The opaque overlay canvas
      this.overlay;
      this.overlayContext;
      this.overlayAlpha = 0;

      // Reference to the redraw animation so it can be cancelled
      this.redrawAnimation;

      // Currently selected region
      this.selectedRegion = { left: 0, top: 0, right: 0, bottom: 0 };

      // Currently cleared region
      this.clearedRegion = { left: 0, top: 0, right: 0, bottom: 0 };

      // Currently pressed down key modifiers
      this.keyModifiers = { ctrl: false, shift: false, alt: false, cmd: false };

      // contains the nodes to be highlighted.
      this.selectedNodes = [];
    }
    FocusController.prototype = {
      initialize: function initialize(options) {
        // TODO: handle options.
        this.options = options || {};
        //this.options.container = $('.article__main').get(0);
        this.options.container = document.body;

        // Only initialize if the client is capable
        if( this.capable() && !this.__fokused ) {

          // Ensures that Fokus isn't initialized twice for this controller.
          this.__fokused = true;

          this.overlay = document.createElement( 'canvas' );
          this.overlayContext = this.overlay.getContext( '2d' );

          // Place the canvas on top of everything
          this.overlay.style.position = 'fixed';
          //this.overlay.style.position = 'absolute';
          this.overlay.style.left = 0;
          this.overlay.style.top = 0;
          this.overlay.style.zIndex = 50;
          this.overlay.style.pointerEvents = 'none';
          this.overlay.style.background = 'transparent';

          document.addEventListener( 'mousedown', this.onMouseDown.bind(this), false );
          document.addEventListener( 'keyup', this.onKeyPress.bind(this), false );
          document.addEventListener( 'keydown', this.onKeyPress.bind(this), false );
          document.addEventListener( 'scroll', this.onScroll.bind(this), false );
          document.addEventListener( 'DOMMouseScroll', this.onScroll.bind(this), false );
          document.body.addEventListener( 'resize', this.onWindowResize.bind(this), false );
          window.addEventListener( 'resize', this.onWindowResize.bind(this), false );

          // Trigger an initial resize
          this.onWindowResize.call(this);

        }

      },

      /**
       * Is this browser capable of running Fokus?
       */
      capable: function capable() {

        return !!(
          'addEventListener' in document &&
          'pointerEvents' in document.body.style
        );

      },

      /**
       * Redraws an animates the overlay.
       */
      redraw: function redraw() {

        // Cache the response of this for re-use below
        var _hasSelection = this.hasSelection();

        this.updateSelection(false, true);

        // Reset to a solid (less opacity) overlay fill
        this.overlayContext.clearRect( 0, 0, this.overlay.width, this.overlay.height );
        this.overlayContext.fillStyle = 'rgba( 0, 0, 0, '+ this.overlayAlpha +' )';
        this.overlayContext.fillRect( 0, 0, this.overlay.width, this.overlay.height );

        if( this.overlayAlpha < 0.01 ) { // TODO: check if 0 instead?
          // Clear the selection instantly if we're just fading in
          this.clearedRegion = this.selectedRegion;
        }
        var animate = false;
        if( animate ) {
          // Ease the cleared region towards the selected selection
          this.clearedRegion.left += ( this.selectedRegion.left - this.clearedRegion.left ) * 0.18;
          this.clearedRegion.top += ( this.selectedRegion.top - this.clearedRegion.top ) * 0.18;
          this.clearedRegion.right += ( this.selectedRegion.right - this.clearedRegion.right ) * 0.18;
          this.clearedRegion.bottom += ( this.selectedRegion.bottom - this.clearedRegion.bottom ) * 0.18;
        }
        else {
          // Ease the cleared region towards the selected selection
          this.clearedRegion.left   = this.selectedRegion.left;
          this.clearedRegion.top    = this.selectedRegion.top;
          this.clearedRegion.right  = this.selectedRegion.right;
          this.clearedRegion.bottom = this.selectedRegion.bottom;
        }

        // Cut out the cleared region
        this.overlayContext.clearRect(
          this.clearedRegion.left - window.scrollX - this.PADDING,
          this.clearedRegion.top - window.scrollY - this.PADDING,
          ( this.clearedRegion.right - this.clearedRegion.left ) + ( this.PADDING * 2 ),
          ( this.clearedRegion.bottom - this.clearedRegion.top ) + ( this.PADDING * 2 )
        );

        // Fade in if there's a valid selection...
        var fade = false;
        if( _hasSelection ) {
          if (fade) {
            this.overlayAlpha += ( this.OPACITY - this.overlayAlpha ) * 0.08;
          }
          else {
            this.overlayAlpha = this.OPACITY;
          }
        }
        // ... otherwise fade out
        else {
          if (fade) {
            this.overlayAlpha = Math.max( ( this.overlayAlpha * 0.85 ) - 0.02, 0 );
          }
          else {
            this.overlayAlpha = 0;
          }
        }

        // Ensure there is no overlap
        cancelAnimationFrame( this.redrawAnimation );

        // Continue so long as there is content selected or we are fading out
        if( _hasSelection || this.overlayAlpha > 0 ) {
          // Append the overlay if it isn't already in the DOM
          //if( !this.overlay.parentNode ) document.body.appendChild( this.overlay );
          if( !this.overlay.parentNode ) {
            this.options.container.appendChild( this.overlay );
          }

          // Stage a new animation frame
          this.redrawAnimation = requestAnimationFrame( this.redraw.bind(this) );
        }
        else {
          this.options.container.removeChild( this.overlay );
        }

      },

      /**
       * Steps through all selected nodes and updates the selected
       * region (bounds of selection).
       *
       * @param {Boolean} immediate flags if selection should happen
       * immediately, defaults to false which means the selection
       * rectangle animates into place from one focus region to the next
       *
       * @param {Boolean} insideRedraw If false or undefined prevents redraw
       * from being fired inside updateSelection, so it will update the
       * selection boundaries, but won't get redrawn.
       */
      updateSelection: function updateSelection( immediate, insideRedraw ) {

        // Default to negative space
        var currentRegion = { left: Number.MAX_VALUE, top: Number.MAX_VALUE, right: 0, bottom: 0 };

        var nodes = this.getSelectedNodes();

        for( var i = 0, len = nodes.length; i < len; i++ ) {
          var node = nodes[i];

          // Select parents of text nodes that have contents
          if( node.nodeName === '#text' && node.nodeValue.trim() ) {
            node = node.parentNode;
          }

          // Fetch the screen coordinates for this element
          var position = this.getScreenPosition( node );

          var x = position.x,
          y = position.y,
          w = node.offsetWidth,
          h = node.offsetHeight;

          // 1. offsetLeft works
          // 2. offsetWidth works
          // 3. Element is larger than zero pixels
          // 4. Element is not <br>
          if( node && typeof x === 'number' && typeof w === 'number' && ( w > 0 || h > 0 ) && !node.nodeName.match( /^br$/gi ) ) {
            currentRegion.left = Math.min( currentRegion.left, x );
            currentRegion.top = Math.min( currentRegion.top, y );
            currentRegion.right = Math.max( currentRegion.right, x + w );
            currentRegion.bottom = Math.max( currentRegion.bottom, y + h );
          }
        }

        // Don't update selection if a modifier is specified but not
        // pressed down, unless there's already a selected region
        if( !this.MODIFIER || this.MODIFIER === 'none' || this.keyModifiers[ this.MODIFIER ] || this.hasSelection() ) {
          this.selectedRegion = currentRegion;
        }

        // If flagged, update the cleared region immediately
        if( immediate ) {
          this.clearedRegion = this.selectedRegion;
        }

        // Start repainting if there is a selected region
        if( this.hasSelection() && !insideRedraw ) {
          this.redraw();
        }

      },

      /**
       * Checks if a region is currently selected.
       */
      hasSelection: function hasSelection() {

        if ( this.selectedNodes.length ) { return true; }
        else { return false; }

      },

      onMouseDown: function onMouseDown( event ) {
      },
      onMouseMove: function onMouseMove( event ) {
      },
      onMouseUp: function onMouseUp( event ) {
      },
      onKeyPress: function onKeyPress( event ) {
      },

      onScroll: function onScroll( event ) {

        this.updateSelection( true );

      },

      /**
       * Make sure the overlay canvas is always as wide and tall as
       * the current window.
       */
      onWindowResize: function onWindowResize( event ) {

        //this.overlay.width = window.innerWidth;
        //this.overlay.height = window.innerHeight;
        this.overlay.width = this.options.container.clientWidth;
        this.overlay.height = this.options.container.clientHeight;

      },

      /**
       * Helper methods for getting selected nodes, source:
       * http://stackoverflow.com/questions/7781963/js-get-array-of-all-selected-nodes-in-contenteditable-div
       */
      getSelectedNodes: function getSelectedNodes() {
        return this.selectedNodes;
      },
      setSelectedNodes: function setSelectedNodes(nodes) {
        if (!(nodes instanceof Array)) { // if a single node.
          nodes = [nodes];
        }
        this.selectedNodes = nodes;
        this.updateSelection();
      },
      addSelectedNodes: function addSelectedNodes(nodes) {
        if (!(nodes instanceof Array)) { // if a single node.
          nodes = [nodes];
        }
        nodes.forEach(function(node) {
          this.selectedNodes.push(node);
        });
        this.updateSelection();
      },
      clearSelectedNodes: function setSelectedNodes() {
        this.selectedNodes = [];
        this.updateSelection();
      },
      getRangeSelectedNodes: function getRangeSelectedNodes( range ) {

        var node = range.startContainer;
        var endNode = range.endContainer;

        // Special case for a range that is contained within a single node
        if (node == endNode) {
          if( node.nodeName === '#text' ) {
            return [node.parentNode];
          }
          return [node];
        }

        // Iterate nodes until we hit the end container
        var rangeNodes = [];
        while (node && node != endNode) {
          rangeNodes.push( node = this.nextNode(node) );
        }

        // Add partially selected nodes at the start of the range
        node = range.startContainer;
        while (node && node != range.commonAncestorContainer) {
          rangeNodes.unshift(node);
          node = node.parentNode;
        }

        return rangeNodes;

      },
      nextNode: function nextNode(node) {

        if (node.hasChildNodes()) {
          return node.firstChild;
        } else {
          while (node && !node.nextSibling) {
            node = node.parentNode;
          }
          if (!node) {
            return null;
          }
          return node.nextSibling;
        }

      },

      /**
       * Gets the x/y screen position of the target node, source:
       * http://www.quirksmode.org/js/findpos.html
       */
      getScreenPosition: function getScreenPosition( node ) {
        var x = document.documentElement.offsetLeft,
        y = document.documentElement.offsetTop;

        if ( node.offsetParent ) {
          do {
            x += node.offsetLeft;
            y += node.offsetTop;
          } while ( (node = node.offsetParent) );
        }

        return { x: x, y: y };
      },
    };
    return FocusController;
  })();

  window.FocusController = FocusController; // TODO: turn into singleton?
})(window);
