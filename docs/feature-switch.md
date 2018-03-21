Feature switch
==============

Creating a new switch
---------------------

In the Django admin, go to Common -> Features -> New and create one.

You can specify if it's only available to staff or super users.

Checking in templates
---------------------

Load the common tags first,

```html
{% load common_tags %}
```

and then

```html
{% with_feature canned-demo %}
<script type="text/javascript" src="{% static 'js/canned-demo.js' %}"></script>
{% end_with_feature %}
```

where `canned-demo` is the slug of the feature you want.

Checking in views
-----------------

You can use the `feature_required` decorator:

```python
from publet.common.decorators import feature_required


@feature_required('canned-demo')
def your_view(request):
    ...
```

Or, with a low-level API

```python
from publet.common.models import Feature, feature_active


def your_view(request):
    if feature_active(request, feature_slug='canned-demo'):
        ...

    # Or if you already have a `Feature` instance
    feature = get_object_or_404(Feature, slug='canned-demo')

    if feature_active(request, feature=feature):
        ...
```

Or, using the request context:

```python
def your_view(request):
    if request.is_feature_active('canned-demo'):
        ...
```

Features are also automatically added to the request context.  This means you
can access them in Python like this:

```python
>>> request.features
>>> [{'slug': 'canned-feature', ...}]
```

or simply as `features` in Django templates.
