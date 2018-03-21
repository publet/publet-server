import json
from base64 import b64decode
from jsonschema.exceptions import ValidationError
from jsonpatch import InvalidJsonPatch, JsonPatchConflict

from django import http
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, get_user_model
from django.core.cache import cache

from publet.projects.models import (
    Publication, NewArticle, NewTheme, render_article, render_theme,
    render_publication
)
from publet.projects.patch import validate_ops
from publet.users.models import PubletApiKey
from publet.groups.models import Group
from publet.utils.utils import (
    DatetimeJSONEncoder, font_to_font_face, get_filepicker_policy,
    get_filepicker_read_policy
)


User = get_user_model()


class Http400(Exception):
    pass


class Http401(Exception):
    pass


class Http403(Exception):
    pass


class Http404(Exception):
    pass


class Http423(Exception):
    pass


class Http500(Exception):
    pass


def get_article_being_edited_key(pk):
    return 'article:edited:{}'.format(pk)


def can_user_edit_article_right_now(pk, user):
    key = get_article_being_edited_key(pk)
    value = cache.get(key)

    if not value:
        return True

    if value and value == user.pk:
        return True

    return False


def set_article_as_being_edited(pk, user):
    key = get_article_being_edited_key(pk)
    cache.set(key, user.pk, timeout=5 * 60)


def get_object_or_response(Model, response, **kwargs):
    try:
        return Model.objects.get(**kwargs)
    except Model.DoesNotExist:
        raise response


def get_object_or_404(Model, **kwargs):
    return get_object_or_response(Model, Http404, **kwargs)


class JSONResponseMixin(object):

    def render_to_json(self, data):
        if hasattr(self,  'render'):
            data = self.render(data)

        if not isinstance(data, str):
            encoded = json.dumps(data, cls=DatetimeJSONEncoder)
        else:
            encoded = data

        return http.HttpResponse(content_type='application/json',
                                 content=encoded)


class APIView(View, JSONResponseMixin):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(APIView, self).dispatch(request, *args, **kwargs)

    def payload(self, request):
        try:
            return json.loads(request.body)
        except ValueError:
            raise Http400('Malformed payload')


class BaseResource(APIView):

    model = None
    requires_authentication = True

    def get_object(self, **kwargs):
        return get_object_or_404(self.model, **kwargs)

    def authenticate(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return

        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_header and auth_header.startswith('Basic '):
            auth_string = auth_header.split(' ')[1]

            try:
                username_key = b64decode(auth_string)
            except TypeError:
                username_key = None

            if username_key:
                username, key = username_key.split(':')

                try:
                    api_key = PubletApiKey.objects.get(key=key,
                                                       user__username=username)
                    request.user = api_key.user
                    return
                except PubletApiKey.DoesNotExist:
                    pass

        if self.requires_authentication:
            raise Http401

    def authorize(self, request, *args, **kwargs):
        return

    def pre_check(self, request, *args, **kwargs):
        """
        This is run once the user has been authenticated and authorized, but
        not before any of the get() or post() methods.  This allows you to
        run any general code with an authorized user.
        """
        return

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        response = None
        origin = request.META.get('HTTP_ORIGIN', '*')

        # TODO: Implement allowed
        request_method = request.method.lower()
        allows = ','.join(['get', 'patch', 'post', 'put']).upper()

        if request_method == 'options':
            response = http.HttpResponse(allows)
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = allows
            response['Allow'] = allows
            return response

        try:
            self.authenticate(request, *args, **kwargs)
            self.authorize(request, *args, **kwargs)
            self.pre_check(request, *args, **kwargs)
            response = super(BaseResource, self).dispatch(request, *args,
                                                          **kwargs)
        except Http400, e:
            response = self.http_400(e)
        except Http401:
            response = self.http_401()
        except Http403, e:
            response = self.http_403(e)
        except Http404:
            response = self.http_404()
        except Http423, e:
            response = self.http_423(e)
        except Http500:
            response = self.http_500()

        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    def http_400(self, reason=''):
        return http.HttpResponseBadRequest(reason)

    def http_401(self, reason=''):
        return http.HttpResponse(status=401)

    def http_403(self, reason=''):
        return http.HttpResponseForbidden(reason)

    def http_404(self):
        return http.HttpResponseNotFound()

    def http_423(self, reason=''):
        return http.HttpResponse(reason, status=423)

    def http_500(self):
        return http.HttpResponseServerError()

    def render(self, obj):
        return obj


class GroupResource(BaseResource):

    model = Group

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        if self.obj not in request.user.get_groups():
            raise Http403()

    def get(self, request, *args, **kwargs):
        return self.render_to_json(self.obj)

    def render(self, obj):
        return obj.json()


class PublicationResource(BaseResource):

    model = Publication

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        member = self.obj.group.get_membership(request.user)

        if not member.can_user_read_group():
            raise Http403()

    def get(self, request, *args, **kwargs):
        return self.render_to_json(self.obj)

    def patch(self, request, *args, **kwargs):
        payload = self.payload(request)

        if not validate_ops(payload):
            raise Http400()

        try:
            self.obj.update(payload)
        except (ValidationError, JsonPatchConflict, InvalidJsonPatch):
            raise Http400()
        return http.HttpResponse(status=202)

    def delete(self, request, *args, **kwargs):
        self.obj.delete()
        return http.HttpResponse(status=204)

    def render(self, obj):
        return render_publication(obj)


class PublicationCollectionResource(BaseResource):

    model = Group

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        if self.obj not in request.user.get_groups():
            raise Http403()

    def get(self, request, *args, **kwargs):
        publications = self.obj.publication_set.all()
        return self.render_to_json(publications)

    def post(self, request, *args, **kwargs):
        payload = self.payload(request)
        payload['group'] = get_object_or_404(Group, **kwargs)
        payload['created_by'] = request.user
        Publication.objects.create(**payload)
        return http.HttpResponse(status=201)

    def render(self, objs):
        return map(lambda pub: pub.json, objs)


class ArticleResource(BaseResource):

    model = NewArticle
    render_function = render_article

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        member = self.obj.publication.group.get_membership(request.user)

        if not member:
            raise Http403()

        if not member.can_user_edit_articles():
            raise Http403()

    def pre_check(self, request, *args, **kwargs):
        if can_user_edit_article_right_now(self.obj.pk, request.user):
            set_article_as_being_edited(self.obj.pk, request.user)
        else:
            raise Http423('Article is locked.')

    def get(self, request, *args, **kwargs):
        return self.render_to_json(self.obj)

    def patch(self, request, *args, **kwargs):
        payload = self.payload(request)

        if not validate_ops(payload):
            raise Http400()

        try:
            self.obj.update(payload)
        except (ValidationError, JsonPatchConflict, InvalidJsonPatch):
            raise Http400()

        return http.HttpResponse(status=202)

    def delete(self, request, *args, **kwargs):
        self.obj.delete()
        return http.HttpResponse(status=204)

    def render(self, article):
        return render_article(article)


class ArticleCollectionResource(BaseResource):

    model = Publication

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        group = self.obj.group
        member = group.get_membership(request.user)

        if not member.can_user_add_article():
            raise Http403()

    def post(self, request, *args, **kwargs):
        payload = self.payload(request)
        payload['publication'] = self.obj
        payload['created_by'] = request.user
        NewArticle.objects.create(**payload)
        return http.HttpResponse(status=201)


class AuthService(APIView):

    def post(self, request, *args, **kwargs):
        payload = self.payload(request)

        if 'username' not in payload or 'password' not in payload:
            return http.HttpResponseBadRequest()

        user = authenticate(username=payload['username'],
                            password=payload['password'])

        if not user:
            return http.HttpResponse(status=401)

        login(request, user)

        out = {
            'username': user.username,
            'key': user.publet_api_key.key
        }

        return self.render_to_json(out)


class ThemeFontResource(BaseResource):

    model = NewTheme

    def authenticate(self, request, *args, **kwargs):
        return

    def get(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)
        fonts = self.obj.data['fonts']
        css = '\n\n'.join(map(font_to_font_face, fonts))
        return http.HttpResponse(content_type='text/css',
                                 content=css)


class ThemeResource(BaseResource):

    model = NewTheme
    render_function = render_theme

    def authorize(self, request, *args, **kwargs):
        self.obj = self.get_object(**kwargs)

        member = self.obj.group.get_membership(request.user)

        if not member:
            raise Http403()

        if not member.can_user_edit_group():
            raise Http403()

    def get(self, request, *args, **kwargs):
        return self.render_to_json(self.obj)

    def patch(self, request, *args, **kwargs):
        payload = self.payload(request)

        if not validate_ops(payload):
            raise Http400()

        try:
            self.obj.update(payload)
        except (ValidationError, JsonPatchConflict, InvalidJsonPatch):
            raise Http400()

        return http.HttpResponse(status=202)

    def delete(self, request, *args, **kwargs):
        self.obj.delete()
        return http.HttpResponse(status=204)

    def render(self, theme):
        return render_theme(theme)


class FilePickerPolicyResource(BaseResource):

    requires_authentication = False

    def get(self, request, *args, **kwargs):
        write_policy, write_signature = get_filepicker_policy()
        read_policy, read_signature = get_filepicker_read_policy()

        obj = {
            'write': {
                'policy': write_policy,
                'signature': write_signature
            },
            'read': {
                'policy': read_policy,
                'signature': read_signature
            }
        }

        return self.render_to_json(obj)


class UserResource(BaseResource):

    model = User

    def get(self, request, *args, **kwargs):
        return self.render_to_json(request.user)

    def render(self, user):
        return user.as_json
