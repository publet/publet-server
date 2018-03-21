import json
from django import template
from django.conf import settings


DEBUG = getattr(settings, 'DEBUG', False)
WORDS = {
    2: 'six',
    3: 'four',
    4: 'three',
    5: 'two',
    6: 'two'
}


BREAKING_WORDS = {
    2: 'eight',
    3: 'one-third',
    4: 'four',
    5: 'one-sixth-column ',
    6: 'one-seventh-column ',
}

register = template.Library()


def is_alpha(value, num):
    if value == 1 or (value - 1) % num == 0:
        return True
    else:
        return False


def is_omega(value, num):
    return value % num == 0


def skeletonify(value):
    """
    Takes a number and converts it to a word, to be used as a skeleton
    class name
    """
    return WORDS.get(value, None)


def skeletonify_breaking(value):
    """
    Takes a number and converts it to a word, to be used as a skeleton
    class name
    """
    return BREAKING_WORDS.get(value, None)


def jsonify(value):
    return json.dumps(value)


class Spaceless(template.base.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        if DEBUG:
            return self.nodelist.render(context)

        from django.utils.html import strip_spaces_between_tags
        return strip_spaces_between_tags(self.nodelist.render(context).strip())


class BreakOut(template.base.Node):

    PRE = "</div></div></div>"
    POST = ('<div class="container">'
            '<div class="twelve columns offset-by-two">'
            '<div class="block">')

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        html = self.nodelist.render(context)
        return '\n'.join([self.PRE, html, self.POST])


@register.tag
def spaceless_with_debug(parser, token):
    """
    This works like the built-in {% spaceless %} tag with the exception
    of only taking effect when DEBUG is off.
    """
    nodelist = parser.parse(('end_spaceless_with_debug',))
    parser.delete_first_token()
    return Spaceless(nodelist)


@register.tag
def with_break_out(parser, token):
    """
    Wrap the enclosed content with HTML.  Close the outer wrapper,
    insert our content and then open up the outer wrapper again.  The
    inner content essentially breaks out of the shell.
    """
    nodelist = parser.parse(('end_with_break_out',))
    parser.delete_first_token()
    return BreakOut(nodelist)


register.filter('is_alpha', is_alpha)
register.filter('is_omega', is_omega)
register.filter('skeletonify', skeletonify)
register.filter('skeletonify_breaking', skeletonify_breaking)
register.filter('json', jsonify)
