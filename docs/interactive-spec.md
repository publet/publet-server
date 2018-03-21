Interactive element specification
=================================

This specification relates to article blocks that are in some way interactive.
This means that they insist of HTML, CSS and Javascript.  At this time, Publet
doesn't have a built-in way to insert these types of blocks, and their
insertion must be completed by a Publet developer.

The following is a guide for interactive graphic designers.  It should help
them create graphics or stories that are easily embeddable in a Publet
publication.

* The HTML for the graphic should be contained within a single element.
* The Javascript should only affect the markup specified by the graphic.
* The Javascript may not override any existing browser functionality (such as
    scrolling, unload event handling, etc).
* The CSS should be properly namespaced for the given markup.
* If the graphic is being ported from an existing page, any necessary base
    styles should be included in the CSS.
* Animations, slideshows, carousels, tooltips, popups, and modals are welcome.
* Use of large images or a large number of images may result in degraded
    performance.
* Publet can't be held responsible for inefficient, browser incompatible or
    buggy code within the interactive graphic.
