(function() {

  var el = window.publetPubEl;
  var BASE = 62;
  var UPPERCASE_OFFSET = 55;
  var LOWERCASE_OFFSET = 61;
  var DIGIT_OFFSET = 48;

  function parse(str) {
    var encode = encodeURIComponent;
    var decode = decodeURIComponent;

    function trim(str) {
      if (str.trim) {
        return str.trim();
      }
      return str.replace(/^\s*|\s*$/g, '');
    }

    if ('string' != typeof str) {
      return {};
    }

    str = trim(str);
    if ('' === str) {
      return {};
    }
    if ('?' == str.charAt(0)) {
      str = str.slice(1);
    }

    var obj = {};
    var pairs = str.split('&');
    for (var i = 0; i < pairs.length; i++) {
      var parts = pairs[i].split('=');
      var key = decode(parts[0]);

      var m = /(\w+)\[(\d+)\]/.exec(key);

      if (m) {
        obj[m[1]] = obj[m[1]] || [];
        obj[m[1]][m[2]] = decode(parts[1]);
        continue;
      }

      obj[parts[0]] = null === parts[1] ? '' : decode(parts[1]);
    }

    return obj;
  }

  function ord(string) {
    var str = string + '',
    code = str.charCodeAt(0);
    if (0xD800 <= code && code <= 0xDBFF) {
      var hi = code;
      if (str.length === 1) {
        return code;
      }
      var low = str.charCodeAt(1);
      return ((hi - 0xD800) * 0x400) + (low - 0xDC00) + 0x10000;
    }
    if (0xDC00 <= code && code <= 0xDFFF) {
      return code;
    }
    return code;
  }

  function trueOrd(c) {
    if ('1234567890'.indexOf(c) > -1) {
      return ord(c) - DIGIT_OFFSET;
    }

    if ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'.indexOf(c) > -1) {
      return ord(c) - UPPERCASE_OFFSET;
    }

    if ('abcdefghijklmnopqrstuvwxyz'.indexOf(c) > -1) {
      return ord(c) - LOWERCASE_OFFSET;
    }
  }

  function encode(key) {
    var intSum = 0;
    var reversedKey = key.split('').reverse().join('');

    for (var i = 0; i < reversedKey.length; i++) {
      intSum = intSum + (trueOrd(reversedKey[i]) * Math.pow(BASE, i));
    }

    return intSum;

  }

  // -----------

  var q = parse(window.location.search);
  var blockId = null;
  
  if (q.publet) {
    blockId = encode(q.publet.slice(2));
  }

  function handleResponse(e) {
    el.style.height = e.data.height + 'px';

    if (e.data.blockOffset) {
      window.scroll(0, el.offsetTop + e.data.blockOffset);
    } else {
      window.scroll(0, el.offsetTop);
    }
  }

  window.addEventListener('message', handleResponse, false);

  function getOriginUrl(url) {
    var a = document.createElement('a');
    a.href = url;
    return a.protocol + '//' + a.hostname;
  }

  el.onload = function() {
    el.contentWindow.postMessage({
      name: 'publication',
      blockId: blockId
    }, getOriginUrl(el.src));
  };

})();
