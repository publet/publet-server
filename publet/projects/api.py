"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import json
import logging
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from tastypie import fields
from tastypie import http
from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.exceptions import Unauthorized, ImmediateHttpResponse, NotFound
from tastypie.resources import ModelResource, Resource
from tastypie.validation import FormValidation
from publet.fonts.models import Font, FontFile
from publet.groups.models import Group, GroupMember
from publet.projects.models import (
    Article, Theme, Type, TextBlock, PhotoBlock, VideoBlock, AudioBlock,
    Publication, Color, Preset, Photo, Asset, Flavor,
    PublicationSocialGateEntry, PDFUpload,
    GateSubmission, NewArticle
)
from publet.projects.forms import (
    PublicationSocialGateEntryForm, GenericGateForm
)
from publet.utils.fn import mapcat
from publet.users.models import PubletApiKey
from publet.feedback.models import Feedback

import stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
logger = logging.getLogger(__name__)

BROKER_USERNAME = getattr(settings, 'BROKER_USERNAME', None)


def convert_post_to_VERB(request, verb):
    """
    Force Django to process the VERB.
    """
    if request.method == verb:
        if hasattr(request, '_post'):
            del(request._post)
            del(request._files)

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = verb
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = verb
        setattr(request, verb, request.POST)

    return request


def convert_post_to_put(request):
    return convert_post_to_VERB(request, verb='PUT')


class AwareDateTimeField(fields.DateTimeField):
    """
    This field is timezone-aware version of TastyPie standard DateTime field

    https://gist.github.com/tadeck/4017093
    """
    def convert(self, value):
        """
        Convert any value stored in this field to the actual ISO-8601 string
        """

        if value is None:
            return None

        if not isinstance(value, basestring):
            # Not fully dehydrated yet
            return value.isoformat()

        # Nothing to do with it
        return value


class PubletApiKeyAuthentication(ApiKeyAuthentication):

    def get_key(self, user, api_key):
        try:
            PubletApiKey.objects.get(user=user, key=api_key)
        except PubletApiKey.DoesNotExist:
            return self._unauthorized()

        return True


# Base

class BaseModelResource(ModelResource):

    def hydrate(self, bundle):
        if bundle.request.user.is_anonymous():
            return bundle

        if hasattr(bundle.obj, 'created_by'):
            bundle.obj.created_by = bundle.request.user

        return bundle

    def obj_delete(self, bundle, **kwargs):
        if not hasattr(bundle.obj, 'delete'):
            try:
                bundle.obj = self.obj_get(bundle=bundle, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance could not be found.")

        self.authorized_delete_detail(
            self.get_object_list(bundle.request), bundle)

        # Before deleting, tell Django who did it
        bundle.obj.created_by = bundle.request.user
        bundle.obj.delete()


# Authorization classes

class UserAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")


class GroupAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        # Filter out groups that this user doesn't belong to.
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return object_list

        return object_list.filter(id__in=user.get_groups())

    def read_detail(self, object_list, bundle):
        group = object_list[0]

        user = bundle.request.user

        if user.is_anonymous() and group.is_api_public:
            return True

        if user.is_anonymous():
            return False

        member = group.get_membership(user)

        if member.can_user_read_group():
            return True
        else:
            raise Unauthorized("Sorry, you don't have access to this group.")

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        # Anyone can create groups.
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        user = bundle.request.user
        group = bundle.obj
        member = group.get_membership(user)

        if member.can_user_edit_group():
            return True
        else:
            raise Unauthorized("Sorry, you can't edit this group.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")


class GroupMemberAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        # Filter out group memberships for groups that this user does not
        # belong to.
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return object_list

        return object_list.filter(group__in=user.get_groups())

    def read_detail(self, object_list, bundle):
        group = object_list[0].group

        user = bundle.request.user
        member = group.get_membership(user)

        if member.can_user_read_group():
            return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        group = bundle.data.get('group', None)

        if not group:
            return

        group = GroupResource().get_via_uri(group, request=bundle.request)

        if not group:
            return

        user = bundle.request.user
        member = group.get_membership(user)

        if member.can_user_edit_members():
            return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        group = object_list[0].group

        user = bundle.request.user
        member = group.get_membership(user)

        if member.can_user_edit_members():
            return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        group = object_list[0].group

        user = bundle.request.user
        member = group.get_membership(user)

        if member.can_user_edit_members():
            return True


class PublicationAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return object_list

        # Filter out publications that belong to groups that this user isn't in
        return object_list.filter(id__in=user.get_publications())

    def read_detail(self, object_list, bundle):
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return True

        # Make sure the user has access to this publication.
        if object_list[0] not in user.get_publications():
            raise Unauthorized("Sorry, you don't have access to this "
                               "publication.")
        else:
            return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        if isinstance(bundle.obj, PDFUpload):
            group = bundle.obj.publication.group
        else:
            group = bundle.obj.group

        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_create_publications():
            return True
        else:
            raise Unauthorized("You can't create publications in this group")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        group = bundle.obj.group
        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_edit_publication_settings():
            return True
        else:
            raise Unauthorized()

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        group = bundle.obj.group
        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_delete_publication():
            return True
        else:
            raise Unauthorized()


class GatePublicationAuthorization(Authorization):

    # TODO: check this to make sure we're not leaking data

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")


class ArticleAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return object_list

        # Filter out articles that belong to groups that this user is not in.
        return object_list.filter(id__in=user.get_articles())

    def read_detail(self, object_list, bundle):
        user = bundle.request.user

        if user.is_superuser or user.is_staff:
            return True

        # Make sure the user has access to this article.
        if object_list[0] not in bundle.request.user.get_articles():
            raise Unauthorized("Sorry, you don't have access to this article.")
        else:
            return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def create_detail(self, object_list, bundle):
        group = bundle.obj.publication.group
        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_add_article():
            return True
        else:
            raise Unauthorized("You can't add articles to this publication")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def update_detail(self, object_list, bundle):
        group = bundle.obj.publication.group
        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_edit_articles():
            return True
        else:
            raise Unauthorized("You can't edit articles in this publication")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not yet implemented.")

    def delete_detail(self, object_list, bundle):
        group = bundle.obj.publication.group
        user = bundle.request.user

        member = group.get_membership(user)

        if member.can_user_delete_articles():
            return True
        else:
            raise Unauthorized("You can't edit articles in this publication")


class TypeAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def create_detail(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not allowed.")


class ThemeAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def create_detail(self, object_list, bundle):
        if not bundle.obj.group.can_user_edit_themes(bundle.request.user):
            raise Unauthorized("Not allowed.")

        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_detail(self, object_list, bundle):
        return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Not allowed.")


class FontAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def create_detail(self, object_list, bundle):
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_detail(self, object_list, bundle):
        return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_detail(self, object_list, bundle):
        if not bundle.obj.theme.group.can_user_edit_themes(
                bundle.request.user):
            raise Unauthorized("Not allowed.")

        return True


# Block authorizations

class BlockAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        # Only return blocks that belong to the user's articles.
        return object_list.filter(
            article__in=bundle.request.user.get_articles())

    def read_detail(self, object_list, bundle):
        user = bundle.request.user
        group = bundle.obj.article.publication.group
        member = group.get_membership(user)

        if member.can_user_edit_articles():
            return True
        else:
            raise Unauthorized("Sorry, you don't have access to this block.")

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def create_detail(self, object_list, bundle):
        # As with the ArticleAuthorization above, Tastypie is going to try and
        # access the Article from the user's existing authorizations. So,
        # creating blocks for articles that the user does not have access to is
        # naturally unauthorized.
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_detail(self, object_list, bundle):
        articles = bundle.request.user.get_articles()

        # Make sure the user has access to this block.
        if bundle.obj.article not in articles:
            raise Unauthorized("Sorry, you don't have access to this block.")

        return self.test_locked(bundle)

    def test_locked(self, bundle):

        if not bundle.obj.is_locked:
            return True

        gm = bundle.obj.article.publication.group.groupmember_set.get(
            user=bundle.request.user)

        if gm.role == 'C':
            raise Unauthorized("Sorry, you don't have access to this block.")

        return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_detail(self, object_list, bundle):
        user = bundle.request.user
        group = bundle.obj.article.publication.group
        member = group.get_membership(user)

        if member.can_user_delete_blocks():
            return True
        else:
            raise Unauthorized("Sorry, you can't delete blocks here.")


class PhotoAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def read_detail(self, object_list, bundle):

        # Make sure the user has access to this block.
        if object_list[0].block.article not in \
                bundle.request.user.get_articles():
            raise Unauthorized("Sorry, you don't have access to this block.")
        else:
            return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def create_detail(self, object_list, bundle):
        # Tastypie will filter the group from the list of authorizated group
        # resource objects, so if the user doesn't have access to the group,
        # they won't have access to the ColorsBlock, and it'll never get here.
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def update_detail(self, object_list, bundle):

        # Make sure the user has access to this block.
        if bundle.obj.block.article not in \
                bundle.request.user.get_articles():
            raise Unauthorized("Sorry, you don't have access to this block.")
        else:
            return True

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Not allowed.")

    def delete_detail(self, object_list, bundle):
        # Make sure the user has access to this block.
        if bundle.obj.block.article not in \
                bundle.request.user.get_articles():
            raise Unauthorized("Sorry, you don't have access to this block.")
        else:
            return True


# Article FKs

class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = UserAuthorization()
        # Not publicly accessible at all, used as ForeignKey
        allowed_methods = []
        fields = ['email', 'username']

        queryset = get_user_model().objects.all()

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(UserResource, self).build_filters(filters)

        if 'account_type' in filters:
            types = filters.getlist('account_type')
            orm_filters['account_type__in'] = types

        return orm_filters


class GroupResource(ModelResource):
    colors = fields.ToManyField('publet.projects.api.ColorResource',
                                'colors', related_name='colors', full=True,
                                null=True)

    class Meta:
        resource_name = 'group'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = GroupAuthorization()
        detail_allowed_methods = ['get', 'put']
        list_allowed_methods = ['get', 'post']
        filtering = {
            'id': ALL,
            'name': ALL,
            'slug': ALL
        }

        queryset = Group.objects.all()
        include_absolute_url = True
        ordering = ['name', '-name']

    def dispatch(self, request_type, request, **kwargs):
        allowed_methods = getattr(self._meta,
                                  "%s_allowed_methods" % request_type, None)

        if 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
            request.method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']

        request_method = self.method_check(request, allowed=allowed_methods)
        method_name = "%s_%s" % (request_method, request_type)
        method = getattr(self, method_name, None)

        if method is None:
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        if method_name != 'get_detail':
            self.is_authenticated(request)

        self.throttle_check(request)

        request = convert_post_to_put(request)
        response = method(request, **kwargs)

        self.log_throttled_access(request)

        if not isinstance(response, HttpResponse):
            return http.HttpNoContent()

        return response

    def get_detail(self, request, **kwargs):
        basic_bundle = self.build_bundle(request=request)

        try:
            obj = self.cached_obj_get(bundle=basic_bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices(
                "More than one resource is found at this URI.")

        if not obj.is_api_public:
            self.is_authenticated(request)

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)

    def dehydrate(self, bundle):
        bundle.data['members_count'] = bundle.obj.members_count
        return bundle

    def obj_create(self, bundle, **kwargs):
        bundle = super(GroupResource, self).obj_create(bundle, **kwargs)
        bundle.obj.save()

        # When a new group is created, set the creator to be the owner of the
        # group.

        owner, _ = GroupMember.objects.get_or_create(user=bundle.request.user,
                                                     group=bundle.obj)
        owner.role = 'O'
        owner.save()

        return bundle

    def obj_update(self, bundle, **kwargs):

        group_to_update = Group.objects.get(id=bundle.data['id'])
        group_plan_id = 'group-{}'.format(group_to_update.id)

        try:
            new_price = float(bundle.data['price'])
        except ValueError:
            new_price = 0

        old_price = group_to_update.price
        new_price = int(new_price * 100)

        def price_is_empty(price):
            return price == 0 or price is None

        if group_to_update.has_stripe_plan() and price_is_empty(new_price):
            # Setting the price to zero means cancelling the plan.
            # Delete all subscribers and then delete the plan.

            logger.info('Deleting plan "{}"'.format(group_to_update.plan_id))

            # TODO: Delete all subscribers from this plan.

            bundle.data['price'] = 0
            bundle.data['plan_id'] = ''
            plan = stripe.Plan.retrieve(group_to_update.plan_id)
            plan.delete()

        elif price_is_empty(old_price) and not price_is_empty(new_price):
            # Didn't have a price set before and now you do
            logger.info('Creating Stripe plan for group "{}"'.format(
                group_to_update.pk))

            new_plan = stripe.Plan.create(
                amount=new_price,
                interval='month',
                name='Group subscription plan for {}'.format(
                    group_to_update.name),
                currency='usd',
                id=group_plan_id)

            bundle.data['plan_id'] = new_plan.id

        else:
            # Changing price which is illegal
            new_price = old_price

        bundle.data['price'] = new_price

        bundle = super(GroupResource, self).obj_update(bundle, **kwargs)
        bundle.obj.save()
        return bundle


class GroupMemberResource(ModelResource):
    group = fields.ForeignKey(GroupResource, 'group')
    user = fields.ForeignKey(UserResource, 'user', full=True)

    class Meta:
        resource_name = 'groupmember'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = GroupMemberAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put', 'post']
        list_allowed_methods = ['get', 'post']
        fields = ['user', 'role']

        queryset = GroupMember.objects.all()

        filtering = {
            'group': ALL_WITH_RELATIONS,
        }

    def dehydrate(self, bundle):
        bundle.data['role_human'] = bundle.obj.get_role_display()
        return bundle

    def obj_create(self, bundle, **kwargs):
        user_uri = bundle.data['user']['resource_uri']
        group_uri = bundle.data['group']

        user = UserResource().get_via_uri(user_uri, request=bundle.request)
        group = GroupResource().get_via_uri(group_uri, request=bundle.request)

        bundle.obj = GroupMember.objects.create(group=group, user=user)

        return bundle

    def obj_update(self, bundle, **kwargs):
        bundle.obj = self.get_via_uri(bundle.data.get('resource_uri'),
                                      request=bundle.request)
        bundle.obj.role = bundle.data.get('role')
        bundle.obj.save()
        return bundle


class ThemeResource(BaseModelResource):
    group = fields.ForeignKey('publet.projects.api.GroupResource',
                              'group', null=True, full=False)
    fonts = fields.ToManyField('publet.projects.api.FontResource',
                               'fonts', null=True, full=True)
    colors = fields.ToManyField('publet.projects.api.ColorResource',
                                'color_set', null=True, full=True)
    background_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                         'background_color', null=True,
                                         full=False)
    link_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                   'link_color', null=True, full=False)
    nav_background_color = fields.ForeignKey(
        'publet.projects.api.ColorResource', 'nav_background_color',
        null=True, full=False)
    nav_font_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                       'nav_font_color', null=True, full=False)
    heading_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                      'heading_color', null=True, full=False)
    toc_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                  'toc_color', null=True, full=False)
    toc_background_color = fields.ForeignKey(
        'publet.projects.api.ColorResource', 'toc_background_color', null=True,
        full=False)
    flavors = fields.ToManyField('publet.projects.api.FlavorResource',
                                 'flavor_set', null=True, full=True)

    class Meta:
        resource_name = 'theme'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = ThemeAuthorization()
        detail_allowed_methods = ['get', 'put']
        list_allowed_methods = ['get', 'post']
        filtering = {
            'id': ALL
        }
        limit = 0
        max_limit = 0
        queryset = Theme.objects.all()

    def get_object_list(self, request):
        group_id = request.META.get('HTTP_GROUP', None)
        themes = Theme.objects.all()

        if group_id:
            themes = themes.filter(group__pk=group_id)

        return themes

    def save(self, bundle, skip_errors=False):
        created = False if bundle.obj.pk else True
        bundle = super(ThemeResource, self).save(bundle, skip_errors)

        if created:
            bundle.obj = bundle.obj.create_defaults()

        return bundle


class TypeResource(ModelResource):

    class Meta:
        resource_name = 'type'

        always_return_data = True
        authentication = Authentication()
        authorization = TypeAuthorization()
        detail_allowed_methods = ['get']
        list_allowed_methods = ['get']

        queryset = Type.objects.all()

    def get_object_list(self, request):
        if request.user.is_basic:
            types = Type.objects.filter(name='Identity')
        else:
            types = Type.objects.all()

        return types

    def dehydrate(self, bundle):
        bundle.data['pagination_display'] = bundle.obj.get_pagination_display()
        return bundle


class PresetResource(ModelResource):
    publication = fields.ForeignKey('publet.projects.api.PublicationResource',
                                    'publication', null=True)

    class Meta:
        resource_name = 'preset'

        always_return_data = True
        authentication = Authentication()
        authorization = TypeAuthorization()
        detail_allowed_methods = ['get']
        list_allowed_methods = ['get']

        queryset = Preset.objects.all()


# Article

class PublicationBaseResource(BaseModelResource):
    group = fields.ForeignKey(GroupResource, 'group')
    type = fields.ForeignKey(TypeResource, 'type', null=True)
    theme = fields.ForeignKey(ThemeResource, 'theme', null=True)
    presets = fields.ToManyField('publet.projects.api.PresetResource',
                                 'presets',
                                 related_name='preset',
                                 readonly=True,
                                 full=True,
                                 null=True)

    articles = fields.ToManyField('publet.projects.api.ArticleResource',
                                  'article_set',
                                  related_name='article',
                                  full=True,
                                  null=True)
    display_status = fields.CharField('get_status_display', readonly=True)

    class Meta:
        resource_name = 'publication'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = PublicationAuthorization()
        detail_allowed_methods = ['delete', 'get', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = Publication.objects.all()
        include_absolute_url = True

        filtering = {
            'group': ALL_WITH_RELATIONS,
        }
        ordering = ['name', '-name']

    def dehydrate(self, bundle):
        group_id = bundle.obj.group.ga_tracking_id or None
        mailchimp_id = bundle.obj.group.mailchimp_account_id or None
        bundle.data['group_ga_tracking_code'] = group_id
        bundle.data['group_mailchimp_account_id'] = mailchimp_id
        bundle.data['has_draft_articles'] = bundle.obj.has_draft_articles()
        bundle.data.pop('nav')
        bundle.data.pop('json')
        return bundle


class PublicationResource(PublicationBaseResource):

    def full_dehydrate(self, bundle, for_list=False):
        use_in = ['all', 'list' if for_list else 'detail']

        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            # If it's not for use in this mode, skip
            field_use_in = getattr(field_object, 'use_in', 'all')
            if callable(field_use_in):
                if not field_use_in(bundle):
                    continue
            else:
                if field_use_in not in use_in:
                    continue

            ###################################################################
            #
            #  _______________
            # < piece of shit >
            #  ---------------
            #         \   ^__^
            #          \  (oo)\_______
            #             (__)\       )\/\
            #                 ||----w |
            #                 ||     ||
            #
            #
            # Tastypie, please don't dehydrate articles.  It makes things go
            # slow.  This entire method is copied from the source.  The only
            # thing that's different is the two lines below.
            #
            ###################################################################
            if field_name == 'articles':
                continue

            # A touch leaky but it makes URI resolution work.
            if getattr(field_object, 'dehydrated_type', None) == 'related':
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            bundle.data[field_name] = field_object.dehydrate(bundle,
                                                             for_list=for_list)

            # Check for an optional method to do further dehydration.
            method = getattr(self, "dehydrate_%s" % field_name, None)

            if method:
                bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)
        return bundle


class BrokerPublicationResource(ModelResource):
    group = fields.ForeignKey(GroupResource, 'group')

    class Meta:
        resource_name = 'broker-publication'
        allowed_methods = ['get']
        queryset = Publication.objects.filter(status='live')
        include_absolute_url = True
        filtering = {
            'group': ALL_WITH_RELATIONS,
        }
        ordering = ['name', '-name']

    def dehydrate(self, bundle):
        obj = bundle.obj
        bundle.data = {
            'name': obj.name,
            'absolute_url': obj.get_share_url(),
            'thumbnail_url': obj.thumbnail,
            'content_type': obj.content_type or None,
            'id': obj.id,
            'topics': obj.topics or None,
            'published': obj.published,
            'featured': obj.featured,
            'group': {
                'id': obj.group.id,
                'name': obj.group.name,
                'slug': obj.group.slug
            }
        }
        return bundle


class FlatPublicationResource(PublicationBaseResource):
    """
    This is a flat version of the publication resource.  Flat means that
    it doesn't include any articles.  This makes larger datasets way
    faster to return.
    """

    def __init__(self, *args, **kwargs):
        super(FlatPublicationResource, self).__init__(*args, **kwargs)
        self._meta.resource_name = 'flat-publication'
        self.fields.pop('articles')


class PublicationWithFlatArticlesResource(PublicationBaseResource):
    articles = fields.ToManyField(
        'publet.projects.api.FlatArticleResource', 'article_set',
        related_name='article', full=True, null=True)

    def __init__(self, *args, **kwargs):
        super(PublicationWithFlatArticlesResource, self).__init__(*args,
                                                                  **kwargs)
        self._meta.resource_name = 'publication-with-flat-articles'


class PublicationWithFlatNewArticlesResource(PublicationBaseResource):
    articles = fields.ToManyField(
        'publet.projects.api.FlatNewArticleResource', 'newarticle_set',
        related_name='article', full=True, null=True)

    def __init__(self, *args, **kwargs):
        super(PublicationWithFlatNewArticlesResource, self).__init__(
            *args, **kwargs)
        self._meta.resource_name = 'publication-with-flat-new-articles'


class ArticleResource(BaseModelResource):
    preset = fields.ForeignKey(PresetResource, 'preset', null=True)
    theme = fields.ForeignKey(ThemeResource, 'theme', null=True, full=True,
                              readonly=True)
    publication = fields.ForeignKey(PublicationResource, 'publication',
                                    null=True)
    modified = AwareDateTimeField('modified')

    # Blocks
    photoblocks = fields.ToManyField('publet.projects.api.PhotoBlockResource',
                                     'photoblock_set',
                                     related_name='photoblock',
                                     full=True,
                                     null=True)

    textblocks = fields.ToManyField('publet.projects.api.TextBlockResource',
                                    'textblock_set',
                                    related_name='textblock',
                                    full=True,
                                    null=True)
    videoblocks = fields.ToManyField('publet.projects.api.VideoBlockResource',
                                     'videoblock_set',
                                     related_name='videoblock',
                                     full=True,
                                     null=True)
    audioblocks = fields.ToManyField('publet.projects.api.AudioBlockResource',
                                     'audioblock_set',
                                     related_name='audioblock',
                                     full=True,
                                     null=True)

    class Meta:
        resource_name = 'article'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = ArticleAuthorization()
        detail_allowed_methods = ['delete', 'get', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = Article.objects.prefetch_related().all()
        include_absolute_url = True

        filtering = {
            'group': ALL_WITH_RELATIONS,
        }
        ordering = ['name', '-name']

    def obj_update(self, bundle, **kwargs):
        types = (
            'textblocks',
            'photoblocks',
            'videoblocks',
            'audioblocks',
        )

        # Clean the blocks

        blocks = mapcat(lambda x: bundle.data.get(x, []), types)

        for block in blocks:
            self.clean_block(block)
            map(self.clean_block, block.get('photos', []))

        bundle.obj = self.get_via_uri(bundle.data.get('resource_uri'),
                                      request=bundle.request)
        bundle = self.full_hydrate(bundle)
        self.is_valid(bundle)

        if bundle.obj.pk:
            self.authorized_update_detail(self.get_object_list(bundle.request),
                                          bundle)
        else:
            self.authorized_create_detail(self.get_object_list(bundle.request),
                                          bundle)

        bundle.obj.save()

        for related_name in types:
            manager_name = '{}_set'.format(related_name[:-1])
            manager = getattr(bundle.obj, manager_name, None)
            objs = bundle.data.get(related_name)

            if not objs:
                continue

            for obj in objs:
                try:
                    instance = manager.get(pk=obj['id'])
                except ObjectDoesNotExist:
                    continue

                instance.apply(obj)
                is_dirty, _ = instance.is_dirty()

                if is_dirty:
                    instance.save()

                # TODO: Make this sadness more general

                if related_name == 'photoblocks':
                    photos = obj['photos']

                    for photo in photos:
                        try:
                            p = instance.photo_set.get(pk=photo['id'])
                        except ObjectDoesNotExist:
                            continue

                        p.apply(photo)
                        p_is_dirty, _ = p.is_dirty()

                        if p_is_dirty:
                            p.save()

                if related_name == 'textblocks':
                    assets = obj['assets']

                    for asset in assets:
                        try:
                            a = instance.asset_set.get(pk=asset['id'])
                        except ObjectDoesNotExist:
                            continue

                        a.apply(asset)
                        a_is_dirty, _ = a.is_dirty()

                        if a_is_dirty:
                            a.save()

        return bundle

    def clean_block(self, block):
        """
        Remove dehydrated fields from a block
        """
        block.pop('type', None)

        block.pop('image_url', None)
        block.pop('preview_url', None)
        block.pop('asset_url', None)
        block.pop('cropped_image_url', None)

        block.pop('small_thumb', None)
        block.pop('big_thumb', None)

        if 'crop_marks' in block:
            cm = block['crop_marks']

            if cm:

                if not isinstance(cm, dict):
                    raise ValueError('Incorrect crop mark data')

                if 'x' not in cm.keys():
                    raise ValueError('Incorrect crop mark data')

                block['crop_marks'] = json.dumps(cm)

    def dehydrate(self, bundle):
        bundle.data['has_draft'] = bundle.obj.has_draft()
        return bundle


class FlatArticleResource(ArticleResource):

    def __init__(self, *args, **kwargs):
        super(FlatArticleResource, self).__init__(*args, **kwargs)
        self._meta.resource_name = 'flat-article'

        fields = ['photoblocks', 'textblocks', 'videoblocks', 'audioblocks',
                  'preset', 'theme']

        for f in fields:
            self.fields.pop(f)


class FlatNewArticleResource(ModelResource):

    def __init__(self, *args, **kwargs):
        super(FlatNewArticleResource, self).__init__(*args, **kwargs)
        self._meta.resource_name = 'flat-new-article'

    class Meta:
        model = NewArticle

    def dehydrate(self, bundle):
        bundle.data['name'] = bundle.obj.name
        bundle.data['has_draft'] = False
        bundle.data['absolute_url'] = bundle.obj.url
        bundle.data['id'] = bundle.obj.pk
        bundle.data['order'] = bundle.obj.order
        return bundle


# Blocks

class FlavorResource(BaseModelResource):
    theme = fields.ForeignKey('publet.projects.api.ThemeResource',
                              'theme', null=False, full=False)
    font = fields.ForeignKey('publet.projects.api.FontResource', 'font',
                             null=True)
    color = fields.ForeignKey('publet.projects.api.ColorResource', 'color',
                              null=True)
    background_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                         'background_color', null=True)

    class Meta:
        resource_name = 'flavor'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = Authorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = Flavor.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        if bundle.obj.alignment == '':
            bundle.data['alignment'] = None

        if bundle.obj.text_alignment == '':
            bundle.data['text_alignment'] = None

        return bundle


class FullFlavorResource(ModelResource):
    theme = fields.ForeignKey('publet.projects.api.ThemeResource',
                              'theme', null=False, full=False)
    font = fields.ForeignKey('publet.projects.api.FontResource', 'font',
                             null=True, full=True)
    color = fields.ForeignKey('publet.projects.api.ColorResource', 'color',
                              null=True, full=True)

    class Meta:
        resource_name = 'full-flavor'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = Authorization()
        allowed_methods = ['get']
        filtering = {
            'theme': ALL_WITH_RELATIONS
        }

        queryset = Flavor.objects.all()

    def dehydrate(self, bundle):
        if bundle.obj.alignment == '':
            bundle.data['alignment'] = None

        if bundle.obj.text_alignment == '':
            bundle.data['text_alignment'] = None

        bundle.data['display'] = {
            'alignment': bundle.obj.get_alignment_display(),
            'text_alignment':
                bundle.obj.get_text_alignment_display().capitalize()
        }

        return bundle

    def serialize_items(self, items):
        bundles = []

        for item in items:
            bundle = self.build_bundle(obj=item)
            bundles.append(self.full_dehydrate(bundle))

        return self.serialize(None, bundles, 'application/json')


class BaseBlockResource(BaseModelResource):
    article = fields.ForeignKey(ArticleResource, 'article', null=False)
    font = fields.ForeignKey('publet.projects.api.FontResource', 'font',
                             null=True)
    color = fields.ForeignKey('publet.projects.api.ColorResource', 'color',
                              null=True)
    flavor = fields.ForeignKey('publet.projects.api.FlavorResource', 'flavor',
                               null=True)

    def dehydrate(self, bundle):
        if bundle.obj.custom_css_classes:
            bundle.data['custom_css_classes'] = \
                bundle.obj.custom_css_classes.replace(',', '')

        bundle.data['social_link'] = bundle.obj.get_social_link()

        return bundle

    def hydrate(self, bundle):
        # Alright, here we go --- yet another tastypie yakshave
        # It's simply not possible to add a dynamic default value for a
        # foreign key relationship.  This is why we need to introduce
        # this hack here.  We manually hydrate the `article` attribute
        # early so that we can look up the default flavor for the
        # current theme (which comes from the article).
        value = self.fields['article'].hydrate(bundle)
        bundle.obj.article = value.obj
        bundle.obj.flavor = bundle.obj.get_default_flavor()
        return bundle


class PhotoBlockResource(BaseBlockResource):
    photos = fields.ToManyField('publet.projects.api.PhotoResource',
                                'photo_set', related_name='gallery', full=True,
                                null=True)

    class Meta:
        resource_name = 'photoblock'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = BlockAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = PhotoBlock.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle = super(PhotoBlockResource, self).dehydrate(bundle)
        bundle.data['type'] = 'photo'
        return bundle


class PhotoResource(ModelResource):
    block = fields.ForeignKey(PhotoBlockResource, 'block', null=False)
    heading_font = fields.ForeignKey('publet.projects.api.FontResource',
                                     'heading_font', null=True)
    heading_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                      'heading_color', null=True)

    description_font = fields.ForeignKey('publet.projects.api.FontResource',
                                         'description_font', null=True)
    description_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                          'description_color', null=True)

    class Meta:
        resource_name = 'photo'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = PhotoAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['post']

        queryset = Photo.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle.data['type'] = 'photo'
        bundle.data['image_url'] = bundle.obj.image_url
        bundle.data['has_caption'] = bundle.obj.has_caption
        bundle.data['crop_marks'] = bundle.obj.get_crop_marks()
        bundle.data['cropped_image_url'] = bundle.obj.cropped_image_url
        return bundle


class TextBlockResource(BaseBlockResource):
    processed_html = fields.CharField('processed_html', readonly=True)
    assets = fields.ToManyField('publet.projects.api.AssetResource',
                                'asset_set', related_name='asset', full=True,
                                null=True)
    background_color = fields.ForeignKey('publet.projects.api.ColorResource',
                                         'background_color', null=True)

    class Meta:
        resource_name = 'textblock'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = BlockAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = TextBlock.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle = super(TextBlockResource, self).dehydrate(bundle)
        bundle.data['type'] = 'text'
        return bundle


class VideoBlockResource(BaseBlockResource):

    class Meta:
        resource_name = 'videoblock'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = BlockAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = VideoBlock.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle = super(VideoBlockResource, self).dehydrate(bundle)
        bundle.data['type'] = 'video'
        bundle.data['preview_url'] = bundle.obj.preview_url
        bundle.data['small_thumb'] = bundle.obj.small_thumb
        bundle.data['big_thumb'] = bundle.obj.big_thumb
        bundle.data['crop_marks'] = bundle.obj.get_crop_marks()
        bundle.data['has_caption'] = bundle.obj.has_caption
        bundle.data['video_id'] = bundle.obj.video_id
        bundle.data['video_type'] = bundle.obj.video_type
        bundle.data['ratio'] = bundle.obj.ratio
        return bundle


class AudioBlockResource(BaseBlockResource):

    class Meta:
        resource_name = 'audioblock'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = BlockAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['get', 'post']

        queryset = AudioBlock.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle = super(AudioBlockResource, self).dehydrate(bundle)
        bundle.data['type'] = 'audio'
        bundle.data['has_caption'] = bundle.obj.has_caption
        return bundle


# Content

class ColorResource(BaseModelResource):
    theme = fields.ForeignKey(ThemeResource, 'theme', null=True)

    class Meta:
        resource_name = 'color'
        authentication = PubletApiKeyAuthentication()
        authorization = FontAuthorization()
        allowed_methods = ['get', 'delete']

        queryset = Color.objects.prefetch_related().all()


class FontFileResource(BaseModelResource):

    class Meta:
        resource_name = 'fontfile'
        authentication = PubletApiKeyAuthentication()
        authorization = FontAuthorization()
        allowed_methods = ['get', 'post', 'put']
        queryset = FontFile.objects.all()


class FontResource(BaseModelResource):
    files = fields.ToManyField('publet.projects.api.FontFileResource', 'files',
                               related_name='files', full=True, null=True)

    class Meta:
        resource_name = 'font'
        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = FontAuthorization()
        allowed_methods = ['get', 'post', 'put']

        queryset = Font.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle.data['css'] = bundle.obj.css
        return bundle


class AssetResource(BaseModelResource):
    block = fields.ForeignKey(TextBlockResource, 'block', null=False)

    class Meta:
        resource_name = 'asset'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = PhotoAuthorization()
        detail_allowed_methods = ['get', 'delete', 'put']
        list_allowed_methods = ['post']

        queryset = Asset.objects.prefetch_related().all()

    def dehydrate(self, bundle):
        bundle.data['type'] = 'asset'
        bundle.data['asset_url'] = bundle.obj.asset_url
        return bundle


# Misc

class CorsResource(Resource):

    def post_list(self, request, **kwargs):
        response = super(CorsResource, self).post_list(request, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def method_check(self, request, allowed=None):
        if allowed is None:
            allowed = []

        request_method = request.method.lower()
        allows = ','.join(allowed).upper()

        if request_method == 'options':
            response = HttpResponse(allows)
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        if request_method not in allowed:
            response = http.HttpMethodNotAllowed(allows)
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        return request_method


class GatePublicationResource(BaseModelResource):

    class Meta:
        resource_name = 'gate-publication'

        always_return_data = True
        authentication = PubletApiKeyAuthentication()
        authorization = GatePublicationAuthorization()
        allowed_methods = ['get', 'post']

        queryset = Publication.objects.all()
        include_absolute_url = True


class PublicationSocialGateEntryResource(ModelResource, CorsResource):
    publication = fields.ForeignKey(
        'publet.projects.api.GatePublicationResource', 'publication',
        null=True, full=False)

    class Meta:
        resource_name = 'gate'
        authorization = Authorization()
        allowed_methods = ['post']
        queryset = PublicationSocialGateEntry.objects.all()
        validation = FormValidation(form_class=PublicationSocialGateEntryForm)

    def obj_create(self, bundle, **kwargs):
        bundle = super(PublicationSocialGateEntryResource, self).obj_create(
            bundle, **kwargs)

        seen_gate = bundle.request.session.get('seen_gate', {})
        seen_gate[bundle.obj.publication.pk] = True
        bundle.request.session['seen_gate'] = seen_gate

        return bundle


class GenericGateResource(ModelResource, CorsResource):
    publication = fields.ForeignKey(
        'publet.projects.api.GatePublicationResource', 'publication',
        null=True, full=False)

    class Meta:
        resource_name = 'generic-gate'
        authorization = Authorization()
        authentication = Authentication()
        allowed_methods = ['post']
        queryset = GateSubmission.objects.all()
        validation = FormValidation(form_class=GenericGateForm)

    def hydrate_data(self, bundle):
        bundle.obj.data = bundle.data['data']
        return bundle

    def obj_create(self, bundle, **kwargs):
        bundle = super(GenericGateResource, self).obj_create(
            bundle, **kwargs)

        seen_gate = bundle.request.session.get('seen_gate', {})
        seen_gate[bundle.obj.publication.pk] = True
        bundle.request.session['seen_gate'] = seen_gate

        return bundle


class PDFUploadResource(BaseModelResource):
    publication = fields.ForeignKey('publet.projects.api.PublicationResource',
                                    'publication', null=False, full=False)

    class Meta:
        resource_name = 'pdf'
        authorization = PublicationAuthorization()
        authentication = PubletApiKeyAuthentication()
        allowed_methods = ['post']
        queryset = PDFUpload.objects.all()


class FeedbackResource(BaseModelResource):

    class Meta:
        resource_name = 'feedback'
        authorization = Authorization()
        allowed_methods = ['post']
        queryset = Feedback.objects.all()

    def obj_create(self, bundle, **kwargs):
        text = bundle.data.get('text', None)
        url = bundle.data.get('url', None)

        if not text or not url:
            return bundle

        text = "{}\n\n({})".format(text, url)
        Feedback.objects.create_feedback(2, text, user=bundle.request.user)

        return bundle


@csrf_exempt
def article_name(request, publication_id, article_id):
    if request.method != 'PUT':
        raise Http404

    publication = get_object_or_404(Publication, pk=publication_id)

    if publication.new_style:
        article = get_object_or_404(NewArticle, pk=article_id)
    else:
        article = get_object_or_404(Article, pk=article_id)

    try:
        data = json.loads(request.body)
    except:
        raise Http404

    article.name = data.get('name')
    article.save()

    return HttpResponse(status=202)
