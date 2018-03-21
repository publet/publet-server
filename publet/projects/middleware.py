import time
import logging

from annoying.functions import get_object_or_None
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.utils.cache import patch_vary_headers

from publet.projects.models import Publication
from publet.utils.metrics import ManualTimer, Meter
from publet.outputs.views import preview_publication_html
from publet.groups.models import Group
from publet.groups.views import profile_detail
from publet.common.models import Feature, feature_active

logger = logging.getLogger(__name__)


ARTICLE_DOMAIN_IGNORED_HOSTS = getattr(
    settings,
    'ARTICLE_DOMAIN_IGNORED_HOSTS',
    []
)
DOMAIN = getattr(settings, 'DOMAIN', None)

SECTIONS = {
    'api': 'api'
}

INSTALLATION = getattr(settings, 'INSTALLATION', None)


User = get_user_model()


class CommonMiddleware(object):

    def process_request(self, request):
        host = request.get_host()
        request.is_custom_domain = host != DOMAIN


class UserAgentMiddleware(object):

    def process_request(self, request):
        agent = request.META.get('HTTP_USER_AGENT', None)

        request.is_iphone = False
        request.is_ipad = False
        request.is_android = False
        request.is_mobile = False

        if not agent:
            return

        if 'iPhone' in agent:
            request.is_iphone = True
            request.is_mobile = True
            return

        if 'iPad' in agent:
            request.is_ipad = True
            request.is_mobile = True
            return

        if 'Android' in agent:
            request.is_android = True
            request.is_mobile = True
            return


class FeatureMiddleware(object):

    def process_request(self, request):
        features = Feature.objects.all()
        features_dict = Feature.objects.as_dict(features)

        def is_feature_active(slug):
            feature = features_dict.get(slug, None)
            return feature_active(request, feature=feature, feature_slug=slug)

        request.is_feature_active = is_feature_active
        request.features = features_dict


class PublicationDomainMiddleware(object):
    """
    This piece of middleware handles custom domain publications and groups

    There are three possible patterns:

    1.  Publication at the root
    2.  Group listing at root and publication at /pub-slug/
    3.  /group-slug/pub-slug/

    If a publication has a domain set, it will be available at

    1.  domain.com
    2.  domain.com/pub-slug/
    3.  domain.com/group-slug/pub-slug/

    If a group has a domain set, the / will have the publication listing.  The
    publication logic from above has precedence over group listing at /.
    """

    def process_request(self, request):
        if request.META.get('SERVER_NAME') == 'testserver':
            return

        request.blog_user = None

        host = request.META.get('HTTP_HOST', '')
        www_host = 'www.' + host

        if host in ARTICLE_DOMAIN_IGNORED_HOSTS:
            return

        if request.path.startswith('/api'):
            return

        if request.path.startswith('/admin'):
            return

        parts = filter(None, request.path.split('/'))

        if len(parts) == 2:

            publication = get_object_or_None(Publication, slug=parts[0],
                                             pagination='h')

            if not publication:
                return

            return preview_publication_html(request,
                                            publication.group.slug,
                                            publication.slug,
                                            page=parts[1])

            # If there are 2 parts to the URL, we assume it's /group/pub/ which
            # can be handled by the normal pipeline.
            return

        if len(parts) == 1:
            # Only ever a publication
            publication_slug = parts[0]
            publication = get_object_or_None(Publication, domain=host,
                                             slug=publication_slug)

            if not publication and 'www' not in host:
                publication = get_object_or_None(Publication, domain=www_host,
                                                 slug=publication_slug)

            if not publication:
                publication = get_object_or_None(Publication,
                                                 group__domain=host,
                                                 slug=publication_slug)

            if not publication and 'www' not in host:
                publication = get_object_or_None(Publication,
                                                 group__domain=www_host,
                                                 slug=publication_slug)

            if publication:
                return preview_publication_html(request,
                                                publication.group.slug,
                                                publication.slug)

            # o hai, maybe it's a publication with pagination turned on?
            publication = get_object_or_None(Publication, domain=host)

            if not publication and 'www' not in host:
                publication = get_object_or_None(Publication, domain=www_host)

            if publication:
                return preview_publication_html(request,
                                                publication.group.slug,
                                                publication.slug,
                                                page=parts[0])

        if len(parts) == 0:
            # This could be either a publication or a group listing.  Let's try
            # publication first.
            publication = get_object_or_None(Publication, domain=host)

            if not publication and 'www' not in host:
                publication = get_object_or_None(Publication, domain=www_host)

            if publication:
                return preview_publication_html(request,
                                                publication.group.slug,
                                                publication.slug)

            group = get_object_or_None(Group, domain=host)

            if group:
                return profile_detail(request, group.slug)

        return redirect('http://publet.com')


class ResponseTimeMiddleware(object):

    def process_request(self, request):
        request.init_time = time.time()
        Meter('requests.started').inc()

        paths = request.path.lstrip('/').split('/')[:2]

        if len(paths) > 0 and paths[0] in SECTIONS:
            request._metrics_section = SECTIONS[paths[0]]
        else:
            request._metrics_section = None

        if 'analytics' in paths:
            request._is_analytics = True

        if request._metrics_section:
            label = 'site-sections.%s-response-time' % request._metrics_section
            Meter(label).inc()

        return None

    def process_response(self, request, response):
        if hasattr(request, "init_time"):
            delta = time.time() - request.init_time
            ms = delta * 1000

            Meter('requests.completed').inc()

            try:
                response_type = response.status_code / 100 * 100
            except:
                response_type = 'unknown'

            Meter('requests.response-types.%s' % response_type).inc()

            response.set_cookie('response_time', str(ms))

            ManualTimer('response-time').record(ms)

            if request._metrics_section:
                label = 'site-sections.%s-response-time' % \
                    request._metrics_section
                ManualTimer(label).record(ms)

            if hasattr(request, '_is_analytics'):
                ManualTimer('site-sections.analytics-response-time').record(ms)

        return response


class ImpersonateMiddleware(object):

    SESSION_KEY = '_impersonate'

    def process_request(self, request):
        if not INSTALLATION:
            return

        if INSTALLATION not in ['dev', 'staging']:
            return

        if not request.user.is_authenticated():
            return

        if not request.user.is_superuser:
            return

        pk = request.session.get(self.SESSION_KEY, None)

        if not pk:
            return

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return

        request.user = user
        request.is_impersonated = True


def should_show_debug_toolbar(request):
    if 'debug' in request.GET:
        return True

    return False


class MultiHostMiddleware(object):

    def process_request(self, request):
        host = request.get_host()

        if host and 'pblt' in host:
            request.urlconf = 'publet.shortener'

    def process_response(self, request, response):
        if getattr(request, "urlconf", None):
            patch_vary_headers(response, ('Host',))

        return response
