from optparse import make_option
from django.core.management.base import BaseCommand
from publet.projects.models import Theme, Color


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--fix',
                    action='store_true',
                    dest='fix',
                    default=False,
                    help='Fix themes as well?'),)

    def handle(self, *args, **kwargs):
        themes = Theme.objects.all()

        incomplete_themes = []

        for t in themes:
            colors = {}

            for f in t._meta.fields:
                if f.__class__.__name__ == 'ForeignKey':
                    if f.related_field.model.__name__ == 'Color':
                        colors[f.name] = getattr(t, f.name)

            for f, v in colors.items():
                if v is None:
                    incomplete_themes.append((t, colors,))

        for t, _ in incomplete_themes:
            print t.slug

        print 'Incomplete theme count:', len(incomplete_themes)

        if not kwargs['fix']:
            return

        print 'Fixing...'

        for t, fields in incomplete_themes:
            self.fix_theme(t, fields)

    def fix_theme(self, t, fields):
        defaults = {
            'link_color': '1C4382',
            'heading_color': '1C4382',
            'nav_background_color': '000000',
            'nav_font_color': 'ffffff',
            'background_color': 'ffffff',
            'header_color': '333333'

        }

        for f, v in fields.items():
            if v:
                continue

            hex_c = defaults[f]

            try:
                color = t.colors.get(hex=hex_c)
            except Color.DoesNotExist:
                color = Color.objects.create(hex=hex_c)
                t.colors.add(color)

            setattr(t, f, color)

        t.save(update_on_disk=False)
