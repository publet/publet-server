(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  // Controllers.
  app.controller('PublicationController',
                 ['$scope', 'PublicationStorage', '$location', 'TypeStorage',
                  'ThemeStorage', 'ArticleStorage', 'SaveService',
                  'PdfImportStorage', 'NewArticleStorage',
                  function($scope, PublicationStorage, $location, TypeStorage,
                           ThemeStorage, ArticleStorage, SaveService,
                           PdfImportStorage, NewArticleStorage) {

    $scope.currentTab = 'articles';
    $scope.currentDataTab = 'audience';

    $(document.body).on( 'click', 'a#new-article-button', function() {
      $('#new-article-name').val('');
      $scope.newArticleName = null;
      $scope.newArticleType = null;
      $('#new-article-type').val('').trigger('chosen:open');
    });

    $(document.body).on( 'click', '.chosen-results li', function () {
      $(this).siblings('li').removeClass('selected');
      $(this).addClass('selected');
    });

    $scope.addingArticle = false;
    $scope.newArticleName = null;

    $scope.addArticle = function() {
      if (window.newStyle) {
        return $scope.addNewArticle();
      }

      if ($scope.newArticle.$invalid) {
        return false;
      }

      $scope.newArticleDisabled = true;

      var newArticle = {
        'group': $scope.publication.group,
        'publication': '/api/publication/' + window.publication_id + '/',
        'name': $scope.newArticleName,
        'theme': $scope.publication.theme,
        'preset': null
      };

      ArticleStorage.addArticle(newArticle).then(function(response) {
        $scope.addingArticle = false;
        $scope.$root.$broadcast('article-added');
        $scope.newArticleName = null;
        $scope.newArticleDisabled = false;
        $scope.getPublication();
      });

    };

    // Add new style article
    $scope.addNewArticle = function() {
      if ($scope.newArticle.$invalid) {
        return;
      }

      $scope.newArticleDisabled = true;

      var newArticle = {
        'name': $scope.newArticleName
      };

      NewArticleStorage.addArticle(window.publication_id,
                                   newArticle).then(function(response) {
        $scope.addingArticle = false;
        $scope.$root.$broadcast('article-added');
        $scope.newArticleName = null;
        $scope.newArticleDisabled = false;
        $scope.getPublication();
        $('#addArticleModal').modal('hide');
      });

    };

    $('#myModal').on('show.bs.modal', function(event) {
      var button = $(event.relatedTarget);
      var recipient = button.data('delete');
      var modal = $(this);
      modal.find('.modal-title').text('Delete "' + recipient.name + '"?');
      $scope.articleBeingDeleted = recipient;
      $scope.deleteModal = modal;

    });

    $scope.deleteArticleProxy = function() {
      $scope.deleteArticle($scope.articleBeingDeleted);
      $scope.deleteModal.modal('hide');

    };

    $scope.deleteArticle = function(article) {
      if (window.newStyle) {
        return $scope.deleteNewArticle(article);
      }
      ArticleStorage.deleteArticle(article).then(function(response) {
        $scope.getPublication();
      });
    };

    $scope.deleteNewArticle = function(article) {
       NewArticleStorage.deleteArticle(article).then(function(response) {
        $scope.getPublication();
       });
    };

    $scope.delete = function() {
      PublicationStorage.deletePublication($scope.publication).then(function(response) {
        window.location = '/groups/';
        $scope.$apply();
      });
    };

    $scope.saveArticleName = function(publication, article) {
      ArticleStorage.saveArticleName(publication, article).then(function() {
        window.location.reload();
      });
    };

    function findDefaultPreset(presets) {
      for (var i = 0; i < presets.length; i++) {
        if (presets[i].name === 'Blank') {
          return presets[i].resource_uri;
        }
      }
    }


    $scope.getPublication = function() {
      if (!window.publication_id) {
        return;
      }

      if (window.newStyle) {
        PublicationStorage.getPublicationWithFlatNewArticles(window.publication_id)
          .then(function(response) {
            $scope.publication = response.data;
            $scope.group = $scope.publication.group;
            $scope.newArticlePreset = findDefaultPreset($scope.publication.presets);
          });
      } else {
        PublicationStorage.getPublicationWithFlatArticles(window.publication_id)
        .then(function(response) {
            $scope.publication = response.data;
            $scope.group = $scope.publication.group;
            $scope.newArticlePreset = findDefaultPreset($scope.publication.presets);
        });
      }
    };
    $scope.getType = function() {
      TypeStorage.getType().then(function(response) {
        $scope.types = response.data.objects;
      });
    };
    $scope.getThemes = function() {
      ThemeStorage.getThemes().then(function(response) {
        $scope.themes = response.data.objects;
      });
    };
    $scope.save = function(form) {
      SaveService.save(form ? form : null, PublicationStorage.savePublication, $scope.publication).then(function(response) {
        // Redirect to the new url if it changed
        if ($scope.publication.absolute_url !== response.data.absolute_url) {
          window.location.href = response.data.absolute_url;
        }

        $scope.publication = response.data;
      });
    };

    // Use the saveFlat function to save the publication when articles aren't
    // involved; this significantly speeds things up when you're simply
    // switching the theme or flipping a flag
    $scope.saveFlat = function(form) {
      SaveService.save(form ? form : null, PublicationStorage.savePublicationFlat, $scope.publication).then(function(response) {
        var articles = $scope.publication.articles;

        // Redirect to the new url if it changed
        if ($scope.publication.absolute_url !== response.data.absolute_url) {
          window.location.href = response.data.absolute_url;
        }

        $scope.publication = response.data;
        $scope.publication.articles = articles;
        window.newStyle = response.data.new_style;
      });

      $scope.editingPublication = false;
    };

    $scope.getPublication();
    $scope.getType();
    $scope.getThemes();
    $scope.statuses = [
      { name: 'Live', value: 'live' },
      { name: 'Hidden', value: 'hidden' },
      { name: 'Pre-order', value: 'preorder' },
      { name: 'Custom', value: 'custom' }
    ];
    $scope.gate_types = [
      {name: 'No gate', value: 'n'},
      {name: 'Delayed', value: 'd'},
      {name: 'Non-strict', value: 'o'},
      {name: 'Strict', value: 's'},
      {name: 'Experiment 1', value: '1'}
    ];
    $scope.pagination = [
      { name: 'Continuous', value: 'c'},
      { name: 'Chapters', value: 'h'}
    ];
    $scope.paginationChoices = [
        { name: 'Single scroll', value: 'c'},
        { name: 'Multiple pages', value: 'h'}
    ];

    $scope.$on('articles-reordered', function() {
      SaveService.save(null, PublicationStorage.reorderPublication, $scope.publication).then(function(response) {
        // TODO: re-order DOM and set order properties based on response
      });
    });

    $scope.selectPdfFile = function() {
      filepicker.pickAndStore(window.FP.write, {}, function(fpfiles) {
        PublicationStorage.savePublicationFlat({
          id: window.publication_id,
          original_pdf_link: fpfiles[0].url,
          original_pdf_filename: fpfiles[0].filename
        }).then(function(response) {
          $scope.publication.original_pdf_filename = fpfiles[0].filename;
          $scope.publication.original_pdf_link = fpfiles[0].url;
        });
      });
      return false;
    };

    $scope.clearPdf = function() {
      PublicationStorage.savePublicationFlat({
        id: window.publication_id,
        original_pdf_link: null,
        original_pdf_filename: null
      }).then(function(response) {
        $scope.publication.original_pdf_filename = null;
        $scope.publication.original_pdf_link = null;
      });

      return false;
    };

    $scope.selectPdfForImport = function() {
      filepicker.pickAndStore(window.FP.write, {}, function(fpfiles) {
        var promise = PdfImportStorage.addPdf(fpfiles[0].filename,
                                              fpfiles[0].url,
                                              window.publication_id);
        promise.then(function(response) {
          window.location.reload();
        });
      });
      return false;
    };


    $scope.duplicatePublication = function(publication) {
      PublicationStorage.duplicatePublication(publication).then(function() {
        alert('Duplicated successfully.');
      });
    };

    $scope.republish = function(publication) {
      PublicationStorage.republishPublication(publication).then(function() {
        alert('Republished successfully.');
      });
    };

    $scope.$watch('publication.type', function(newValue, oldValue) {
      if ($scope.types !== undefined) {
        var type = _.find($scope.types, function(el) {
          return el.resource_uri === newValue;
        });
        $scope.pagination = type.pagination_display;
      }
    });

    $scope.linkTextPublication_zip = 'Download HTML';
    $scope.linkTextPublication_pdf = 'Download PDF';
    $scope.linkTextPublication_epub = 'Download ePub';
    $scope.linkTextPublication_mobi = 'Download MOBI';
    $scope.linkTextPublication_ios = 'Download iOS';

    $scope.renderPublication = function(extension, $event) {
      $scope['linkTextPublication_' + extension] = 'Please wait...';

      var interval;

      function checker() {
        PublicationStorage.renderPublication($scope.publication, extension).then(function(response) {
          if (response.data.status === 'ready') {
            clearInterval(interval);
            $scope['linkTextPublication_' + extension] = 'Done! Click to download.';
            $event.target.href = response.data.path;
          }
        });
      }

      interval = setInterval(checker, 5000);
      checker();

      return false;
    };

    function secondsToMinutes(s) {
      s = Math.floor(s);
      var over, minutes;

      if (s < 60) {
        return s + 's';
      }

      if (s < (60 * 60)) {

        over = s % 60;
        minutes = (s - over) / 60;

        return minutes + 'min ' + over + 's';

      }

      var overHour = s % 3600;
      var hours = (s - overHour) / 3600;

      over = (s - (hours * 3600)) % 60;
      minutes = (s - (hours * 3600) - over) / 60;

      return hours + 'h ' + minutes + 'min ' + over + 's';

    }

    function getIconFromType(type) {
      return window.icons[type];
    }

    function setupEngagedGraphs() {

      var categories = [];
      var c = 1;
      var vals = [];

      _.each(window.engaged.articles, function(obj, key) {
        vals.push(obj.value);
        categories.push(c);
        c++;
      });

      var series = [{
        name: 'Articles',
        data: vals,
        type: 'column'
      }];

      $scope.chartConfig = {
        options: {
          tooltip: {
            formatter: function() {
              return 'Article ' + this.x + ': ' + secondsToMinutes(this.point.y);
            }
          },
          chart: {
            type: "areaspline"
          },
          plotOptions: {} // This needs to stay; otherwise, tooltips break (JAVASCRIPT!)
        },
        xAxis: {
          categories: categories
        },
        yAxis: {
          title: {
            text: 'Minutes'
          },
          min: 0,
          labels: {
            formatter: function() {
              return secondsToMinutes(this.value);
            }
          }
        },
        series: series,
        title: {
          text: "Engaged time"
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };

    }

    function setupPercentReadGraphs() {

      var categories = [];
      var c = 1;
      var vals = [];

      _.each(window.read.articles, function(obj, key) {
        vals.push(obj.value);
        categories.push(c);
        c++;
      });

      var series = [{
        name: 'Articles',
        data: vals,
        type: 'column'
      }];

      $scope.readChartConfig = {
        options: {
          tooltip: {
            formatter: function() {
              return 'Article ' + this.x + ': ' + this.y + '%';
            }
          },
          chart: {
            type: "areaspline"
          },
          plotOptions: {} // This needs to stay; otherwise, tooltips break (JAVASCRIPT!)
        },
        xAxis: {
          categories: categories
        },
        yAxis: {
          min: 0,
          labels: {
            formatter: function() {
              return this.value + '%';
            }
          }
        },
        series: series,
        title: {
          text: "% read"
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };

    }

    function setupSocialGraphs() {

      function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.slice(1);
      }

      var data = [];

      _.each(window.social, function(val, key) {
        data.push([capitalize(key), val]);
      });

      $scope.socialChartConfig = {
        options: {
          plotOptions: {
            pie: {
              allowPointSelect: true,
              cursor: 'pointer',
              dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: {point.y} - {point.percentage:.1f} %'
              }
            }
          }
        },
        series: [{
          type: 'pie',
          name: 'Number of referrals',
          data: data,
        }],
        title: {
          text: ""
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };
    }

    function setupSocialReferralGraph() {
      var categories = [];
      var series = [];

      var a = {
        twitter: [],
        facebook: [],
        linkedin: [],
        googleplus: []
      };

      _.each(window.socialReferrals, function(v, k) {
        _.each(a, function(__, network) {
          a[network].push(v.values[network] || 0);
        });
        categories.push({
          id: v.id,
          type: v.type
        });
      });

      _.each(a, function(v, k) {
        series.push({
          name: k,
          data: v
        });
      });

      $scope.socialReferralChart = {
        options: {
          tooltip: {
            useHTML: true,
            formatter: function() {
              return '<a href="/internal/block/' + this.key.id + '" target="_blank">View block</a>';
            }
          },
          chart: {
            type: 'column'
          },
          plotOptions: {
            series: {
              stacking: 'normal'
            }
          }
        },
        yAxis: {
          min: 0
        },
        xAxis: {
          categories: categories,
          labels: {
            useHTML: true,
            formatter: function() {
              var src = getIconFromType(this.value.type);
              if (!src) {
                return '';
              }
              return '<img src="' + src + '" />';
            }
          }
        },
        series: series,
        title: {
          text: ''
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };

    }

    function setupSocialReferralPerBlockGraph() {
      var series = [];
      var categories = [];

      var a = {
        twitter: [],
        facebook: [],
        linkedin: [],
        googleplus: []
      };

      _.each(window.socialReferralsPerBlock, function(v, k) {
        _.each(a, function(__, network) {
          a[network].push(v.values[network] || 0);
        });
        categories.push({
          id: v.id,
          type: v.type
        });
      });

      _.each(a, function(v, k) {
        series.push({
          name: k,
          data: v
        });
      });

      $scope.socialReferralChartPerBlock = {
        options: {
          tooltip: {
            useHTML: true,
            formatter: function() {
              return '<a href="/internal/block/' + this.key.id + '" target="_blank">View block</a>';
            }
          },
          chart: {
            type: 'column'
          },
          plotOptions: {
            series: {
              stacking: 'normal'
            }
          }
        },
        yAxis: {
          min: 0,
          stackLabels: {
            enabled: true
          }
        },
        xAxis: {
          categories: categories,
          labels: {
            useHTML: true,
            formatter: function() {
              var src = getIconFromType(this.value.type);
              return '<img src="' + src + '" />';
            }
          }
        },
        series: series,
        title: {
          text: ''
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };

    }

    function setupDropoffGraph() {
      var categories = [];
      var c = 1;
      var vals = [];

      _.each(window.dropoff, function(obj, key) {
        vals.push(obj[1]);
        categories.push(c);
        c++;
      });

      var series = [{
        name: 'Articles',
        data: vals,
        type: 'column'
      }];

      $scope.dropoffConfig = {
        options: {
          tooltip: {
            formatter: function() {
              return 'Article ' + this.x + ': ' + this.point.y + ' sessions';
            }
          },
          chart: {
            type: "areaspline"
          },
          plotOptions: {} // This needs to stay; otherwise, tooltips break (JAVASCRIPT!)
        },
        xAxis: {
          categories: categories
        },
        yAxis: {
          title: {
            text: 'Number of sessions'
          },
          min: 0
        },
        series: series,
        title: {
          text: "Dropoff report"
        },
        credits: {
          enabled: false
        },
        loading: false,
        size: {}
      };

    }

    function setupGraphs() {
      setupEngagedGraphs();
      setupPercentReadGraphs();
      setupSocialGraphs();
      setupSocialReferralGraph();
      setupSocialReferralPerBlockGraph();
      setupDropoffGraph();
    }

    if (window.engaged) {
      setupGraphs();
    }

  }]);

  // Directives.
  app.directive('publication', [function() {
    return {
      compile: function compile(elm, attrs, transclude) {
        return {
          post: function post(scope, elm, attrs) {

            // Sortable blocks.
            $('table#article-table tbody').sortable({
              handle: '.reorder',
              stop: function() {

                var $articles = $('.tr-article');

                // Set order on articles according to where they are in the DOM.
                for (var i = 0; i < $articles.length; i++) {
                  var articleScope = angular.element($articles.eq(i).get(0)).scope();
                  articleScope.article.order = i;
                }

                scope.$root.$broadcast('articles-reordered');

              }
            });

          }
        };
      }
    };
  }]);

})(window);
