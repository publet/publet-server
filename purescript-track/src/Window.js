// module Window

exports.windowSignalImpl =
  function windowSignalImpl(constant) {
    return function(eventName) {
      return function() {
        var out = constant(false);
        window.addEventListener(eventName, function(e) {
          out.set(true);
        });
        return out;
      };
    };
  };

