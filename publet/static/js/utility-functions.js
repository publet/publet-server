function contains(s, match) {
  return s.indexOf(match) > -1;
}

function containsAny(url, matches) {
  for (var i = 0; i < matches.length; i++) {
    if (contains(url, matches[i])) {
      return true;
    }
  }

  return false;
}
