(function(window) {

  // jQuery.
  var $ = window.jQuery;

  // Get the app.
  var app = window.app;

  // Controllers.
  app.controller('GroupController',
                 ['$scope', '$timeout', 'GroupStorage', 'GroupMemberStorage', 'ArticleStorage', 'TypeStorage', 'ThemeStorage', 'UserStorage', 'PublicationStorage',
                  function($scope, $timeout, GroupStorage, GroupMemberStorage, ArticleStorage, TypeStorage, ThemeStorage, UserStorage, PublicationStorage) {
    $scope.newPublicationName = null;
    $scope.newPublicationType = null;
    $scope.newPublicationTheme = null;

    $scope.typeOptions = [
      {name: 'Owner', value: 'O'},
      {name: 'Editor', value: 'E'},
      {name: 'Contributor', value: 'C'},
      {name: 'Reviewer', value: 'R'}
    ];

    $scope.memberEditing = function(member) {
      var m = _.find($scope.groupMembers, function(el) {
        return el.resource_uri === member.resource_uri;
      });

      if (!m) {
        return false;
      }

      if (m.editing && m.editing === true) {
        return true;
      }

      return false;
    };

    $scope.saveNewMemberRole = function(member) {
      GroupMemberStorage.saveMember(member).then(function(response) {
        var humanRole = _.find($scope.typeOptions, function(el) {
          return el.value === member.role;
        });
        member.editing = false;
        member.role_human = humanRole.name;
      });
    };

    $scope.toggleMemberEditing = function(member) {
      var m = _.find($scope.groupMembers, function(el) {
        return el.resource_uri === member.resource_uri;
      });

      if (m.editing) {
        m.editing  = false;
      } else {
        m.editing  = true;
      }

    };

    $scope.candidateNotFound = false;
    $scope.missingUser = null;
    $scope.findUser = function() {
      $scope.candidate = _.find($scope.addableUsers, function(el) {
        return (el.username === $scope.usernameToFind ||
                el.email === $scope.usernameToFind);
      });

      if (!$scope.candidate) {
        $scope.candidateNotFound = true;
        $scope.missingUser = angular.copy($scope.usernameToFind);
      } else {
        $scope.candidateNotFound = false;
        $scope.missingUser = null;
      }
    };

    $scope.addToGroup = function() {
      GroupMemberStorage.addUserToGroup($scope.candidate, $scope.group).then(function(response) {
        $scope.groupMembers.push(response.data);
        $scope.candidate = null;
      });
    };

    $scope.removeMember = function(member) {
      GroupMemberStorage.deleteGroupMember(member).then(function() {
        var index = _.find($scope.groupMembers, function(el) {
          return el.resource_uri === member.resource_uri;
        });

        $scope.groupMembers.splice(index, 1);

      });
    };

    $scope.inviteButtonText = 'Send invite';
    $scope.saveUserInviteForm = function() {
      var users = $scope.inviteFirstName + ',' +
            $scope.inviteLastName + ',' + $scope.inviteEmail;

      $scope.inviteButtonText = 'Sending...';
      UserStorage.createEmailInvites(window.group_id, users, $scope.inviteRole).then(function() {
        $scope.inviteRole = null;
        $scope.inviteFirstName = '';
        $scope.inviteLastName = '';
        $scope.inviteEmail = '';
        $scope.inviteButtonText = 'Sent!';

        $timeout(function() {
          $scope.inviteButtonText = 'Send invite';
        }, 2000);

      });

      return false;
    };

    /*  New Publication Modal Interactions */
    $(document.body).on( 'click', 'a#new-publication-button', function() {
      $('#new-publication-name').val('');
      $scope.newPublicationName = null;
      $scope.newPublicationTheme = null;
      $scope.newPublicationType = null;
      $('#new-publication-type').val('').trigger('chosen:open');
      $('#new-publication-theme').val('').trigger('chosen:open');
    });

    $scope.$watch('newPublicationName', function(newValue, oldValue) {
      if ($scope.error && newValue !== null) {
        $scope.error = null;
      }
    });

    $(document.body).on( 'click', '.chosen-results li', function () {
      $(this).siblings('li').removeClass('selected');
      $(this).addClass('selected');
    });

    $scope.addingArticle = false;
    $scope.newGroupName = null;
    $scope.newPublicationName = null;
    $scope.newArticleName = null;

    $scope.apiOptions = [
      {value: 'n', name: 'No API'},
      {value: 'p', name: 'Public API'},
      {value: 'r', name: 'Private API'}
    ];

    $scope.duplicatePublication = function(publication) {
      PublicationStorage.duplicatePublication(publication).then(function() {
        alert('Duplicated successfully.');
      });
    };

    $scope.deletePublication = function(publication) {
      var c = confirm('Are you sure?');

      if (!c) {
        return;
      }

      PublicationStorage.deletePublication(publication).then(function(response) {
        window.location.reload();
      });
    };

    $scope.addPublication = function() {

      if ($scope.newPublication.$invalid) {
        $scope.error = true;
        return;
      }

      $scope.newPublicationDisabled = true;

      var newPublication = {
        'group': '/api/group/' + $scope.group.id + '/',
        'name': $scope.newPublicationName,
        'type': $scope.newPublicationType,
        'theme': $scope.newPublicationTheme
      };

      PublicationStorage.addPublication(newPublication).then(function(response) {
        window.location = '/groups/' + $scope.group.slug + '/publications/' + response.data.slug + '/';
        return;
      });

    };

    $scope.addArticle = function() {

      if ($scope.newArticle.$invalid) {
        return;
      }

      $scope.newArticleDisabled = true;

      var newArticle = {
        'group': '/api/group/' + $scope.group.id + '/',
        'name': $scope.newArticleName,
        'type': $scope.newArticleType,
        'theme': $scope.newArticleTheme
      };

      ArticleStorage.addArticle(newArticle).then(function(response) {
        $scope.addingArticle = false;
        $scope.$root.$broadcast('article-added');
        $scope.newArticleName = null;
        $scope.newArticleDisabled = false;
      });

    };
    $scope.getAddableUsers = function() {
      UserStorage.getBasicAndPro().then(function(response) {

        $scope.addableUsers = [];

        // This could probably be optimized further.
        var users = response.data.objects;
        users.forEach(function(user) {

          var isGroupMember = false;
          $scope.groupMembers.some(function(groupMember) {
            if (groupMember.user.username === user.username) {
              isGroupMember = true;
              return;
            }
          });

          if (!isGroupMember) {
            $scope.addableUsers.push(user);
          }
        });

      });
    };
    $scope.getGroup = function() {
      GroupStorage.getGroup(window.group_id).then(function(response) {
        $scope.group = response.data;
      });
    };
    $scope.getGroupMembers = function() {
      GroupMemberStorage.getGroupMembers(window.group_id).then(function(response) {
        $scope.groupMembers = response.data.objects;
        $scope.getAddableUsers();
      });
    };
    $scope.getPublications = function() {
      PublicationStorage.getPublications($scope.group, true).then(function(response) {
        $scope.publications = response.data.objects;
      });
    };
    $scope.getType = function() {
      TypeStorage.getType().then(function(response) {
        $scope.type = response.data.objects;
      });
    };
    $scope.getThemes = function() {
      ThemeStorage.getThemes().then(function(response) {
        $scope.themes = response.data.objects;
      });
    };
    $scope.save = function() {

      $scope.saveGroupDisabled = true;

      if ($scope.saveGroup.$invalid) {
        return;
      }

      GroupStorage.saveGroup($scope.group).then(function(response) {
        if ($scope.group.absolute_url !== response.data.absolute_url) {
          window.location.href = response.data.absolute_url;
        }
        $scope.group = response.data;
        $scope.saveGroupDisabled = false;
      });

    };

    $scope.getType();
    $scope.getThemes();

    // Get the group details and then fetch articles for the group.
    GroupStorage.getGroup(window.group_id).then(function(response) {
      $scope.group = response.data;
      $scope.getPublications();
      $scope.getGroupMembers();
    });

    $scope.$root.$on('article-added', function() { $scope.getGroup(); });
    $scope.$root.$on('article-deleted', function() { $scope.getGroup(); });

    $scope.$watch('newUserToGroup', function(newUserToGroup) {

      if (newUserToGroup) {
        GroupMemberStorage.addUserToGroup(newUserToGroup,
                                          $scope.group).then(function() {
                                            $scope.getGroupMembers();
                                          });
      }

      // Reset the new-user-to-group select.
      $scope.newUserToGroup = null;
      $scope.$root.$broadcast('user-added-to-group');

    });

    $scope.selectLogoFile = function() {
      filepicker.pickAndStore(window.FP.write, {}, function(fpfiles) {
        $scope.group.logo = fpfiles[0].url;
        $scope.group.logo_filename = fpfiles[0].filename;
        GroupStorage.saveGroup($scope.group);
      });
      return false;
    };

    $scope.clearLogo = function() {
      $scope.group.logo = null;
      GroupStorage.saveGroup($scope.group);
    };

    $scope.selectFaviconFile = function() {
      filepicker.pickAndStore(window.FP.write, {}, function(fpfiles) {
        $scope.group.favicon = fpfiles[0].url;
        $scope.group.favicon_filename = fpfiles[0].filename;
        GroupStorage.saveGroup($scope.group);
      });
      return false;
    };

    $scope.clearFavicon = function() {
      $scope.group.favicon = null;
      GroupStorage.saveGroup($scope.group);
    };

  }]);
  app.controller('GroupsController', ['$scope', 'GroupStorage', function($scope, GroupStorage) {

    $scope.addingGroup = false;
    $scope.newGroupName = null;

    $scope.allGroups = [];

    function rebuildPagination(groups) {
      $scope.groups = groups;
    }

    $scope.search = function(value) {
      value = value.toLowerCase();
      var filtered = _.filter($scope.allGroups, function(el) {
        return el.name.toLowerCase().indexOf(value) > -1;
      });

      rebuildPagination(filtered);
    };

    $scope.addGroup = function() {

      if ($scope.newGroup.$invalid) {
        return;
      }

      $scope.newGroupDisabled = true;

      var newGroup = {
        'name': $scope.newGroupName
      };

      GroupStorage.addGroup(newGroup).then(function(response) {
        window.location.href = response.data.absolute_url;
      });
    };
    $scope.getGroups = function() {
      GroupStorage.getGroups().then(function(groups) {
        $scope.allGroups = groups.data.objects;
        rebuildPagination($scope.allGroups);
      });
    };

    $scope.getGroups();

  }]);
  app.controller('GroupMemberController', ['$scope', 'GroupMemberStorage', function($scope, GroupMemberStorage) {

    // Don't let users edit themselves, yet.
    $scope.editable = $scope.member.user.username !== window.user;

    $scope.remove = function() {

      if (window.confirm('Are you sure you want to remove “' +
                         $scope.member.user.username + '” from the “' +
                           $scope.group.name + '“ group?')) {
        GroupMemberStorage.deleteGroupMember($scope.member).then(
          function(response) {
          $scope.getGroupMembers();
        });
      }

    };
  }]);

  app.controller('InviteByEmailController', ['$scope', 'UserStorage', '$timeout', function($scope, UserStorage, $timeout) {
    $scope.valid = true;
    $scope.typeOptions = [
      {name: 'Owner', value: 'O'},
      {name: 'Editor', value: 'E'},
      {name: 'Contributor', value: 'C'},
      {name: 'Reviewer', value: 'R'}
    ];

    function validateCSV(data) {
      for (var i = 0; i < data.length; i++) {
        if (data[i].length !== 3) {
          return false;
        }

        if (data[i][2] === '') {
          return false;
        }
      }

      return true;
    }

    $scope.inviteUsers = function() {
      if (!$scope.users) {
        $scope.valid = false;
        return;
      }

      var csv = CSV.parse($scope.users);
      $scope.valid = validateCSV(csv);

      if (!$scope.userType) {
        $scope.valid = false;
      }

      if ($scope.valid) {
        UserStorage.createEmailInvites(
          window.group_id,
          $scope.users,
          $scope.userType).then(function() {
            $scope.users = '';
            $scope.userType = '?';
            $scope.valid = true;
            $scope.done = true;
            $timeout(function() {
              $scope.done = false;
            }, 2000);
          });
      }
    };
  }]);

  // Directives.
  app.directive('group', ['GroupStorage', function(GroupStorage) {
    return {
      compile: function compile(elm, attrs, transclude) {
        return {
          post: function post(scope, elm, attrs) {}
        };
      }
    };
  }]);
  app.directive('newUserToGroup', [function() {
    return {
      compile: function compile(elm, attrs, transclude) {
        return {
          post: function post(scope, elm, attrs) {
            scope.$watch('addableUsers', function() {
              elm.trigger('chosen:updated');
            });
            scope.$on('user-added-to-group', function() {
              scope.newUserToGroup = null;
              elm.trigger('chosen:updated');
            });
          }
        };
      }
    };
  }]);

})(window);
