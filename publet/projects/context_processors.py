from django.conf import settings
from django.contrib.auth import get_user_model
from publet.utils.utils import (
    get_filepicker_policy, get_filepicker_read_policy
)
from publet.utils.fn import ip2int


CURRENT_COMMIT = getattr(settings, 'CURRENT_COMMIT', None)
INSTALLATION = getattr(settings, 'INSTALLATION', None)
INTERCOM_APP_ID = getattr(settings, 'INTERCOM_APP_ID', None)
HOST = getattr(settings, 'HOST', None)
SHORT_HOST = getattr(settings, 'SHORT_HOST', None)
GOOGLE_ANALYTICS_ID = getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
USE_LIVE_RELOAD = getattr(settings, 'USE_LIVE_RELOAD', False)
FILEPICKER_API_KEY = getattr(settings, 'FILEPICKER_API_KEY', None)
TRACK_URL = getattr(settings, 'TRACK_URL', None)


def add_current_commit(request):
    if request.user.is_superuser and CURRENT_COMMIT:
        return dict(current_commit=CURRENT_COMMIT,
                    current_commit_abbr=CURRENT_COMMIT[:5])

    return {}


def add_intercom(request):
    return {
        'INTERCOM_APP_ID': INTERCOM_APP_ID
    }


def add_filepicker_policy(request):
    if request.user.is_authenticated():
        policy, signature = get_filepicker_policy()
        read_policy, read_signature = get_filepicker_read_policy()

        data = {
            'write': dict(policy=policy, signature=signature),
            'read': dict(policy=read_policy, signature=read_signature)
        }

        return dict(filepicker=data)

    return {}


def add_host(request):
    return {
        'HOST': HOST,
        'SHORT_HOST': SHORT_HOST,
        'INSTALLATION': INSTALLATION
    }


def add_google_analytics_id(request):
    return {
        'GOOGLE_ANALYTICS_ID': GOOGLE_ANALYTICS_ID
    }


def add_livereload(request):
    return {
        'USE_LIVE_RELOAD': USE_LIVE_RELOAD
    }


def add_all_users(request):
    if not request.user.is_authenticated():
        return {}

    if not request.user.is_superuser:
        return {}

    return {
        'users': get_user_model().objects.all().order_by('email')
    }


def add_filepicker_api_key(request):
    return {
        'FILEPICKER_API_KEY': FILEPICKER_API_KEY
    }


def add_ip_as_int(request):
    ip = request.META.get('HTTP_X_REAL_IP')
    return {
        'ip_as_int': ip2int(ip)
    }


def add_can_impersonate(request):
    return {
        'can_impersonate': INSTALLATION in ['dev', 'staging']
    }


def add_features(request):
    return {
        'features': request.features
    }


def add_track_host(request):
    return {
        'track_url': TRACK_URL
    }
