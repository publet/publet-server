from django import template

register = template.Library()


def stripify(value):
    # TODO: this is really dumb. Force publication price to cents somewhere
    # else.
    return str(value).replace('.', '')

register.filter('stripify', stripify)
