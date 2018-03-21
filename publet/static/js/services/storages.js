(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  app.factory('ArticleStorage', ['api', function(api) {
    return {
      addArticle: function(article) {
        return api.POST({
          url: '/api/article/',
          data: article
        });
      },
      deleteArticle: function(article) {
        return api.DELETE({
          url: '/api/article/' + article.id + '/'
        });
      },
      getArticle: function(article_id) {
        return api.GET({
          url: '/api/article/' + article_id + '/'
        });
      },
      getArticles: function(group) {
        return api.GET({
          url: '/api/article/' + (group ? '?group=' + group.id + '&order_by=name&limit=0' : '?order_by=name&limit=0')
        });
      },
      saveArticle: function(article) {
        return api.PUT({ // returns a $q promise.
          url: '/api/article/' + article.id + '/',
          data: {
            resource_uri: article.resource_uri,
            domain: article.domain,
            hosted_password: article.hosted_password,
            gate_copy: article.gate_copy,
            group: article.group,
            name: article.name,
            type: article.type,
            preset: article.preset,

            photoblocks: article.photoblocks,
            textblocks: article.textblocks,
            videoblocks: article.videoblocks,
            audioblocks: article.audioblocks

          }
        });
      },
      saveArticleName: function(publication, article) {
        return api.PUT({ // returns a $q promise.
          url: '/api/article-name/' + publication.id + '/' + article.id + '/',
          data: {
            name: article.name
          }
        });
      },
      reorderArticle: function(article) {
        var blocks = _.sortBy([].concat(
            article.photoblocks,
            article.textblocks,
            article.videoblocks,
            article.audioblocks),
          _.property('order')).map(function (block) {
            return [block.type, block.id];
          });
        return api.POST({
          url: '/api/article/' + article.id + '/reorder/',
          data: {
            block_type_ids: blocks
          }
        });
      },
      renderArticle: function(article, extension) {
        return api.POST({
          url: '/outputs/request/',
          no_authorization: true,
          data: {
            'article_pk': article.id,
            'extension': extension
          }
        });
      }
    };
  }]);

  app.factory('NewArticleStorage', ['api', function(api) {
    return {
      addArticle: function(publicationId, article) {
        return api.POST({
          url: '/api/2/publication/' + publicationId + '/articles/',
          data: article
        });
      },
      deleteArticle: function(article) {
        return api.DELETE({
          url: '/api/2/article/' + article.id + '/'
        });
      },
    };
  }]);

  app.factory('TypeStorage', ['api', function(api) {
    return {
      getType: function(group) {
        return api.GET({
          no_authorization: true,
          url: '/api/type/'
        });
      }
    };
  }]);
  app.factory('FontStorage', ['api', function(api) {
    return {
      addFont: function(font) {
        return api.POST({
          url: '/api/font/',
          data: font
        });
      }
    };
  }]);
  app.factory('ColorStorage', ['api', function(api) {
    return {
      removeColor: function(colorId) {
        return api.DELETE({
          url: '/api/color/' + colorId + '/'
        });
      }
    };
  }]);
  app.factory('FlavorStorage', ['api', function(api) {
    return {
      addFlavor: function(flavor) {
        return api.POST({
          url: '/api/flavor/',
          group: true,
          data: flavor
        });
      },
      removeFlavor: function(flavorId) {
        return api.DELETE({
          url: '/api/flavor/' + flavorId + '/',
          group: true
        });
      }
    };
  }]);
  app.factory('ThemeStorage', ['api', function(api) {
    return {
      getThemes: function() {
        return api.GET({
          url: '/api/theme/',
          group: true
        });
      },

      addTheme: function(name, group) {
        return api.POST({
          url: '/api/theme/',
          group: true,
          data: {
            name: name,
            group: group
          }
        });
      },

      saveTheme: function(theme) {
        return api.PUT({
          url: '/api/theme/' + theme.id + '/',
          group: true,
          data: theme
        });
      }
    };
  }]);

  app.factory('PublicationStorage', ['api', function(api) {
    return {
      addPublication: function(publication) {
        return api.POST({
          url: '/api/publication/',
          group: true,
          data: publication
        });
      },
      deletePublication: function(publication) {
        return api.DELETE({
          url: '/api/publication/' + publication.id + '/'
        });
      },
      getPublication: function(publication_id) {
        return api.GET({
          url: '/api/publication/' + publication_id + '/'
        });
      },
      getPublicationWithFlatArticles: function(publication_id) {
        return api.GET({
          url: '/api/publication-with-flat-articles/' + publication_id + '/'
        });
      },
      getPublicationWithFlatNewArticles: function(publication_id) {
        return api.GET({
          url: '/api/publication-with-flat-new-articles/' + publication_id + '/'
        });
      },
      getPublications: function(group, flat) {
        var resource;

        if (flat) {
          resource = '/api/flat-publication/';
        } else {
          resource = '/api/publication/';
        }

        return api.GET({
          url: resource + (group ? '?group=' + group.id + '&order_by=name&limit=0' : '?order_by=name&limit=0')
        });
      },
      reorderPublication: function(publication) {
        // Send an Array of all Article ids in display order,
        // let the backend decide what the actual 'order' fields should be.
        var article_ids = _.sortBy(publication.articles, _.property('order')).map(_.property('id'));
        return api.POST({
          url: '/api/publication/' + publication.id + '/reorder/',
          data: {article_ids: article_ids}
        });
      },
      savePublication: function(publication) {
        return api.PUT({
          url: '/api/publication/' + publication.id + '/',
          group: true,
          data: publication
        });
      },
      savePublicationFlat: function(publication) {
        return api.PUT({
          url: '/api/flat-publication/' + publication.id + '/',
          group: true,
          data: publication
        });
      },
      duplicatePublication: function(publication) {
        return api.POST({
          url: '/api/publication/' + publication.id + '/duplicate/'
        });
      },
      republishPublication: function(publication) {
        return api.POST({
          url: '/api/publication/' + publication.id + '/republish/'
        });
      },
      renderPublication: function(publication, extension) {
        return api.POST({
          url: '/outputs/request/',
          data: {
            'publication_pk': publication.id,
            'extension': extension
          }
        });
      }
    };
  }]);

  app.factory('BlockStorage', ['api', function(api) {
    return {
      addBlock: function(type, article, order) {
        return api.POST({
          url: '/api/' + type + 'block/',
          data: {
            article: article.resource_uri,
            order: order
          }
        });
      },
      addTextBlock: function(article, order, content) {
        return api.POST({
          url: '/api/textblock/',
          data: {
            article: article.resource_uri,
            order: order,
            content: content
          }
        });
      },
      removeBlock: function(block) {
        return api.DELETE({
          url: '/api/' + block.type + 'block/' + block.id + '/'
        });
      },
      submitToIntegration: function(block, integrationSlug) {
        return api.POST({
          url: '/api/integration-submission/' + block.type + 'block/' +
            block.id + '/',
          data: {
            integration: integrationSlug
          }
        });
      }
    };
  }]);

  app.factory('GroupStorage', ['api', function(api) {

    return {
      addGroup: function(group) {
        return api.POST({
          url: '/api/group/',
          data: group
        });
      },
      getGroup: function(group_id) {
        return api.GET({
          url: '/api/group/' + group_id + '/'
        });
      },
      getGroups: function() {
        return api.GET({
          url: '/api/group/?limit=0&order_by=name'
        });
      },
      saveGroup: function(group) {
        return api.PUT({
          url: '/api/group/' + group.id + '/',
          data: group
        });
      }
    };
  }]);
  app.factory('GroupMemberStorage', ['api', function(api) {
    return {
      addUserToGroup: function(user, group) {
        return api.POST({
          url: '/api/groupmember/',
          data: {
            group: group.resource_uri,
            user: user
          }
        });
      },
      deleteGroupMember: function(member) {
        return api.DELETE({
          url: member.resource_uri
        });
      },
      saveMember: function(member) {
        return api.PUT({
          url: member.resource_uri,
          data: member
        });
      },
      getGroupMembers: function(group_id) {
        return api.GET({
          url: '/api/groupmember/?group=' + group_id
        });
      }
    };
  }]);
  app.factory('UserStorage', ['api', function(api) {
    return {
      getBasicAndPro: function() {
        return api.GET({
          url: '/api/user/basic-and-pro/'
        });
      },

      createEmailInvites: function(group, users, type) {
        return api.POST({
          url: '/account/bulk-invite/',
          data: JSON.stringify({
            group: group,
            users: users,
            type: type
          })
        });
      }

    };
  }]);

  app.factory('AssetStorage', ['api', function(api) {
    return {
      addAsset: function(block, url) {
        return api.POST({
          url: '/api/asset/',
          data: {
            block: block.resource_uri,
            filename: url
          }
        });
      },
      removeAsset: function(asset) {
        return api.DELETE({
          url: '/api/asset/' + asset.id + '/',
        });
      },
      saveAsset: function(asset) {
        return api.PUT({
          url: '/api/asset/' + asset.id + '/',
          data: asset
        });
      }
    };
  }]);

  app.factory('PhotoStorage', ['api', function(api) {
    return {
      addPhoto: function(block, url) {
        return api.POST({
          url: '/api/photo/',
          data: {
            block: block.resource_uri,
            image: url
          }
        });
      },
      removePhoto: function(photo) {
        return api.DELETE({
          url: '/api/photo/' + photo.id + '/'
        });
      }
    };
  }]);

  app.factory('PdfImportStorage', ['api', function(api) {
    return {
      addPdf: function(filename, url, publicationId) {
        return api.POST({
          url: '/api/pdf/',
          data: {
            filename: filename,
            url: url,
            publication: '/api/publication/' + publicationId + '/'
          }
        });
      }
    };
  }]);

  app.factory('FeedbackStorage', ['api', function(api) {
    return {
      send: function(text, url) {
        return api.POST({
          url: '/api/feedback/',
          data: {
            text: text,
            url: url
          }
        });
      }
    };
  }]);

})(window);
