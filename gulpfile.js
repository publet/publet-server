var gulp = require('gulp');
var templateCache = require('gulp-angular-templatecache');

// Compile HTML templates for angular

gulp.task('templates', function() {
  var config = {
    standalone: true,
    root: '/static/js/partials/'
  };

  gulp.src('publet/static/js/partials/*.html')
    .pipe(templateCache(config))
    .pipe(gulp.dest('publet/static/js/'));
});
