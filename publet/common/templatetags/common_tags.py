from django import template


register = template.Library()


def pad(n):
    if n < 10:
        return '0' + str(n)

    return str(n)


def minutes(seconds):
    if seconds in (0, None, ''):
        return '0s'

    if isinstance(seconds, float):
        seconds = round(seconds)

    seconds = int(seconds)

    if seconds < 60:
        return str(seconds) + 's'

    over = seconds % 60
    minutes = (seconds - over) / 60

    return str(minutes) + 'min ' + str(over) + 's'


class WithFeature(template.base.Node):

    def __init__(self, nodelist, feature_slug):
        self.nodelist = nodelist
        self.feature_slug = feature_slug

    def render(self, context):
        request = context.get('request')

        if not request.is_feature_active(self.feature_slug):
            return ''

        return self.nodelist.render(context)


def with_feature(parser, token):
    _, format_string = token.split_contents()
    nodelist = parser.parse('end_with_feature')
    parser.delete_first_token()
    return WithFeature(nodelist, format_string)


register.filter('minutes', minutes)
register.tag('with_feature', with_feature)
