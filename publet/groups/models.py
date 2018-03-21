from django.db.models import Q
from django.db import models, connection
from django.conf import settings

from publet.utils.utils import slugify_with_hash, get_filepicker_read_policy
from publet.utils.metrics import Timer
from publet.common.models import CDNMixin, BaseModel
from publet.common.fields import FilePickerField

User = settings.USER_MODEL
FILEPICKER_READ_POLICY, FILEPICKER_READ_SIGNATURE = \
    get_filepicker_read_policy()


API_SETTING_CHOICES = (
    ('n', 'No API',),
    ('p', 'Public API',),
    ('r', 'Private API',),
)


def superuser_override(f):
    """
    A decorator for permission methods
    """
    def wrapper(self):
        if self.user.is_superuser or self.user.is_staff:
            return True
        else:
            return f(self)

    return wrapper


def requires(role, *args):
    choices = ('O', 'E', 'C', 'R',)

    for arg in args:
        assert arg in choices, "unknown role"

    return role in args


class SuperUserGroupMember(object):

    role = 'O'

    def __init__(self, user):
        self.user = user

    def can_user_edit_group(self):
        return True

    def can_user_edit_members(self):
        return True

    def can_user_read_group(self):
        return True

    def can_user_invite_users_to_group(self):
        return True

    def can_user_create_publications(self):
        return True

    def can_user_edit_publication_settings(self):
        return True

    def can_user_delete_publication(self):
        return True

    def can_user_view_publication_data(self):
        return True

    def can_user_download_formats(self):
        return True

    def can_user_make_publication_comments(self):
        return True

    def can_user_add_article(self):
        return True

    def can_user_edit_articles(self):
        return True

    def can_user_delete_articles(self):
        return True

    def can_user_delete_blocks(self):
        return True

    def can_user_reorder_articles(self):
        return True

    def can_user_edit_themes(self):
        return True


class GroupManager(models.Manager):
    def average_publications_per_group(self):
        query = """
        with counts as (
            select groups_group.slug,count(*) from groups_group
                join projects_publication on
                    (projects_publication.group_id = groups_group.id)
            group by groups_group.slug
        )

        select avg(count) from counts;
        """
        with Timer('sql.analytics.average-publications-per-group'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows


class Group(models.Model, CDNMixin):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    plan_id = models.CharField(max_length=100, default='', blank=True,
                               null=True)
    # In pennies
    price = models.IntegerField(null=True, blank=True, default=0)

    domain = models.CharField(max_length=255, null=True, blank=True)
    favicon = FilePickerField(null=True, blank=True)
    favicon_filename = models.CharField(max_length=255, null=True, blank=True)

    # Google Analytics tracking ID without the campaign suffix
    ga_tracking_id = models.CharField(max_length=20, blank=True)
    mailchimp_account_id = models.CharField(max_length=255, blank=True)
    sharpspring_id = models.CharField(max_length=255, blank=True)
    splyt_id = models.CharField(max_length=255, blank=True)

    # Social
    twitter = models.CharField(max_length=200, blank=True)
    facebook = models.CharField(max_length=200, blank=True)
    pinterest = models.CharField(max_length=200, blank=True)
    linkedin = models.CharField(max_length=200, blank=True)

    api = models.CharField(max_length=1, default='n',
                           choices=API_SETTING_CHOICES)

    # Landing page settings
    has_publish_dates = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    logo = FilePickerField(null=True, blank=True)
    logo_filename = models.CharField(max_length=255, null=True, blank=True)

    # Meta
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    objects = GroupManager()

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self._original_name = self.name

    def __unicode__(self):
        return self.name

    @property
    def has_favicon(self):
        return self.favicon is not None

    def get_absolute_url(self):
        return '/groups/{}/'.format(self.slug)

    def get_members(self):
        return self.groupmember_set.all()

    def get_active_publications(self):
        return self.publication_set.filter(Q(status='preorder') |
                                           Q(status='live'))

    @property
    def members_count(self):
        return self.get_members().count()

    def get_membership(self, user, ignore_superuser=False):
        if user.is_anonymous():
            return

        if (user.is_superuser or user.is_staff) and not ignore_superuser:
            return SuperUserGroupMember(user)

        try:
            return GroupMember.objects.filter(group=self, user=user)[0]
        except IndexError:
            return None

    def can_user_edit(self, user):
        membership = self.get_membership(user)

        if membership and membership.role in ['A', 'O', 'D']:
            return True

        return False

    def can_user_edit_themes(self, user):
        membership = self.get_membership(user)

        if not membership:
            return False

        return membership.can_user_edit_themes()

    def is_user_subscribed(self, user):
        return self.purchase_set.filter(purchase_type='subscription',
                                        user=user).exists()

    def get_landing_template(self):
        return 'outputs/group-landing.html'

    def get_search_result_template(self):
        return 'outputs/group-search-results.html'

    def get_splash_template(self):
        return 'outputs/group-splash.html'

    def get_splash_publication(self):
        try:
            return self.publication_set.filter(
                type__name='Group landing page')[0]
        except IndexError:
            return None

    @property
    def colors(self):
        return []

    def save(self, *args, **kwargs):
        self.ensure_cdn_links('logo')
        self.ensure_cdn_links('favicon')

        if not self.slug or (self._original_name != self.name):
            self.slug = slugify_with_hash(self.name)

        created = False if self.pk else True

        super(Group, self).save(*args, **kwargs)

        if created:
            self.create_default_theme()

    @property
    def is_api_public(self):
        return self.api == 'p'

    @property
    def is_api_private(self):
        return self.api == 'r'

    @property
    def is_api_disabled(self):
        return not self.is_api_enabled

    @property
    def is_api_enabled(self):
        return self.is_api_public or self.is_api_private

    def create_default_theme(self):
        from publet.projects.models import Theme, NewTheme
        Theme.create_default_theme_for_group(self)
        NewTheme.create_default_theme_for_group(self)

    def get_default_theme(self):
        t = self.theme_set.filter(name='Default')

        if t:
            return t[0]

        from publet.projects.models import Theme
        return Theme.create_default_theme_for_group(self)

    def get_default_new_theme(self):
        from publet.projects.models import NewTheme
        t, _ = NewTheme.objects.get_or_create(group=self, name='Default')
        return t

    @property
    def has_domain(self):
        if self.domain:
            return True

    def get_integrations(self):
        return self.integration_set.all()

    def has_stripe_plan(self):
        return self.plan_id != ''

    def has_logo(self):
        return self.logo is not None

    def json(self):
        return {
            'id': self.pk,
            'name': self.name,
            'slug': self.slug,
            'plan_id': self.plan_id,
            'price': self.price,
            'domain': self.domain,
            'twitter': self.twitter,
            'facebook': self.facebook,
            'pinterest': self.pinterest,
            'linkedin': self.linkedin,
            'logo': self.logo,
            'description': self.description,
            'created': self.created,
            'modified': self.modified
        }

    def logo_url(self):
        if not self.has_logo():
            return ''

        return '%s?signature=%s&policy=%s' % (
            self.logo,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    def favicon_url(self):
        if not self.has_favicon:
            return ''

        return '%s?signature=%s&policy=%s' % (
            self.favicon,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)


class GroupMember(models.Model):

    ROLES = (
        ('O', 'Owner'),
        ('E', 'Editor'),
        ('C', 'Contributor'),
        ('R', 'Reviewer'),

        # Deprecated
        ('A', 'Admin'),
        ('D', 'Developer'),
    )

    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    role = models.CharField(max_length=1, choices=ROLES, default='C')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'{}, {} for {}'.format(self.user.username,
                                       self.get_role_display(),
                                       self.group.name)

    class Meta:
        unique_together = (('user', 'group'),)

    @superuser_override
    def can_user_edit_group(self):
        return requires(self.role, 'O')

    @superuser_override
    def can_user_edit_members(self):
        return requires(self.role, 'O')

    @superuser_override
    def can_user_read_group(self):
        return requires(self.role, 'O', 'E', 'C', 'R')

    @superuser_override
    def can_user_invite_users_to_group(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_create_publications(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_edit_publication_settings(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_delete_publication(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_view_publication_data(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_download_formats(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_make_publication_comments(self):
        return True

    @superuser_override
    def can_user_add_article(self):
        return requires(self.role, 'O', 'E', 'C')

    @superuser_override
    def can_user_edit_articles(self):
        return requires(self.role, 'O', 'E', 'C')

    @superuser_override
    def can_user_delete_articles(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_delete_blocks(self):
        return requires(self.role, 'O', 'E')

    @superuser_override
    def can_user_reorder_articles(self):
        return requires(self.role, 'O', 'E', 'C')

    @superuser_override
    def can_user_edit_themes(self):
        return requires(self.role, 'O')


class GroupHub(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    group = models.ForeignKey(Group)
    publications = models.ManyToManyField('projects.Publication')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_with_hash(self.name)

        super(GroupHub, self).save(*args, **kwargs)
