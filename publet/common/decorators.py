from functools import wraps
from django.http import Http404

from models import feature_active


def feature_required(slug):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if feature_active(request, slug):
                return view_func(request, *args, **kwargs)

            raise Http404

        return _wrapped_view

    return decorator
