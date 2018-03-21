import os
import json
import sys
from datetime import datetime
from tempfile import mkdtemp
import platform

import requests
from fabric.api import cd, lcd, local, env, run, sudo, task, settings, hide
from fabric.operations import put, get
from fabric.contrib.files import exists
from fabric.network import disconnect_all
from fabric.colors import cyan, red


USE_FUSION = os.environ.get('PUBLET_USE_FUSION', False)
USE_VMLESS = os.environ.get('PUBLET_USE_VMLESS', False)
FUSION_IP = os.environ.get('PUBLET_FUSION_IP', None)
CHROME_PATH = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

env.is_vagrant = False
env.is_vmless = False
env.platform = 'Linux'  # To match the output of `platform.system()`


def _die(msg):
    sys.stderr.write(red(msg) + '\n')
    sys.exit(1)


def _sanity():
    try:
        assert os.getcwd() == os.path.dirname(os.path.abspath(__file__))
    except AssertionError:
        _die("You're doing it wrong. Run this from the root.")


_sanity()


def is_osx():
    return env.platform == 'Darwin'


def is_linux():
    return env.platform == 'Linux'


def ssh_config(name=''):
    """
    Get the SSH parameters for connecting to a vagrant VM.
    """
    with settings(hide('running')):
        output = local('vagrant ssh-config %s' % name, capture=True)

    config = {}
    for line in output.splitlines()[1:]:
        key, value = line.strip().split(' ', 2)
        config[key] = value
    return config


def get_current_branch():
    branch = local('git rev-parse --abbrev-ref HEAD', capture=True)
    return branch.replace('* ', '')


def assert_correct_branch():
    branch = get_current_branch()
    betas = ['beta', 'production', 'master']
    staging = ['master', 'staging']

    if env.branch in ['lb', 'metrics']:
        return

    if branch in betas and env.branch in betas:
        return

    if branch in staging and env.branch in staging:
        return

    if 'feature' in branch and env.remote in staging:
        return

    _die('Wrong branch!')


def release_in_place():
    branch = get_remote_branch()

    if 'release' in branch:
        return True


def settings_dict(config):
    settings = {}

    user = config['User']
    hostname = config['HostName']
    port = config['Port']

    # Build host string
    host_string = "%s@%s:%s" % (user, hostname, port)

    settings['user'] = user
    settings['hosts'] = [host_string]
    settings['host_string'] = host_string

    # Strip leading and trailing double quotes introduced by vagrant 1.1
    settings['key_filename'] = config['IdentityFile'].strip('"')

    settings['forward_agent'] = (config.get('ForwardAgent', 'no') == 'yes')
    settings['disable_known_hosts'] = True

    return settings


def pip(cmd):
    return env.venv_path.rstrip('/') + '/bin/pip ' + cmd


def python(cmd):
    return env.venv_path.rstrip('/') + '/bin/python ' + cmd


def managepy(cmd):
    if env.is_vmless:
        return 'python manage.py %s --settings=publet.settings_osx' % cmd
    else:
        return python('manage.py %s --settings=publet.%s' % (
            cmd, env.settings_file))


def display_message(message, extra_line=True):
    underline = '-' * len(message)

    if extra_line:
        msg = '\n{}\n{}\n\n'.format(message, underline)
    else:
        msg = '{}\n={}n\n'.format(message, underline)

    try:
        sys.stderr.write(cyan(msg))
    except ImportError:
        print(msg)


def assert_command_exists(cmd, exit=True, msg=None):
    with settings(hide('stdout'), warn_only=True):
        r = local('which %s' % cmd)

        if r.failed:

            if not exit:
                return False

            if not msg:
                msg = 'Please install {} first'.format(cmd)

            _die(msg)
        else:
            return True


def set_hostname(hostname):
    sudo('hostname %s' % hostname)
    sudo('echo %s > /etc/hostname' % hostname)
    sudo('echo "127.0.0.1 %s" > /etc/hosts' % hostname)


def upload_project_sudo(local_dir=None, remote_dir=""):
    """
    Copied from Fabric and updated to use sudo.
    """
    local_dir = local_dir or os.getcwd()

    # Remove final '/' in local_dir so that basename() works
    local_dir = local_dir.rstrip(os.sep)

    local_path, local_name = os.path.split(local_dir)
    tar_file = "%s.tar.gz" % local_name
    target_tar = os.path.join(remote_dir, tar_file)
    tmp_folder = mkdtemp()

    try:
        tar_path = os.path.join(tmp_folder, tar_file)
        local("tar -czf %s -C %s %s" % (tar_path, local_path, local_name))
        put(tar_path, target_tar, use_sudo=True)
        with cd(remote_dir):
            try:
                sudo("tar -xzf %s" % tar_file)
            finally:
                sudo("rm -f %s" % tar_file)
    finally:
        local("rm -rf %s" % tmp_folder)


def ensure_virtualenv():
    if not exists(env.venv_path):
        create_virtualenv()


def get_current_datetime():
    now = datetime.utcnow()
    return now.strftime('%Y%m%d-%H%M%S')


def as_user(user, cmd):
    return run('sudo su %s -c "%s"' % (user, cmd))


# -----------------------------------------------------------------------------
# Environments
# -----------------------------------------------------------------------------

@task
def base():
    env.is_lb = False
    env.is_varnish = False
    env.requires_ubuntu_user = True


@task
def beta(username, branch=None):
    base()
    env.username = username
    env.site_path = '/opt/publet/apps/publet'
    env.apps_path = '/opt/publet/apps'
    env.jar_path = '/opt/publet/jars'
    env.bin_path = '/opt/publet/bin'
    env.venv_path = '/opt/publet/venvs/publet'
    env.bower_dir = os.path.join(env.site_path, 'publet/static')
    env.settings_file = 'settings_beta'
    env.remote = 'beta'
    env.branch = 'master'  # IMPORTANT: Always master
    env.host = 'beta-2.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)
    env.publications_bucket = 'publications-beta'


@task
def beta_varnish(username, branch=None):
    base()
    beta(username, branch)
    env.is_varnish = True
    env.requires_ubuntu_user = False
    env.host = 'publications.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)


@task
def staging_varnish(username, branch=None):
    base()
    staging(username, branch)
    env.is_varnish = True
    env.requires_ubuntu_user = True
    env.host = 'publications-staging.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)


@task
def staging(username, branch='master'):
    base()
    env.username = username
    env.site_path = '/opt/publet/apps/publet'
    env.apps_path = '/opt/publet/apps'
    env.jar_path = '/opt/publet/jars'
    env.bin_path = '/opt/publet/bin'
    env.venv_path = '/opt/publet/venvs/publet'
    env.bower_dir = os.path.join(env.site_path, 'publet/static')
    env.settings_file = 'settings_staging'
    env.remote = 'staging'
    env.branch = branch
    env.host = 'staging-2.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)
    env.publications_bucket = 'publications-staging'


@task
def metrics(username):
    base()
    env.username = username
    env.site_path = '/opt/publet/apps/publet'
    env.venv_path = '/opt/publet/venvs/publet'
    env.bower_dir = os.path.join(env.site_path, 'publet/static')
    env.remote = 'metrics'
    env.host = 'metrics-2.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)
    env.branch = 'metrics'


@task
def lb(username):
    base()
    env.is_lb = True
    env.username = username
    env.host = 'lb-2.publet.com'
    env.port = 41041
    env.host_string = '%s@%s:%s' % (username, env.host, env.port)
    env.branch = 'lb'


@task
def vagrant(name=''):
    base()

    if USE_FUSION:
        return fusion(name)

    if USE_VMLESS:
        return vmless()

    name = ''

    assert_command_exists('vagrant')
    env.is_vagrant = True

    status = local('vagrant status --machine-readable', capture=True)
    status_lines = status.split('\n')

    status = None

    for line in status_lines:
        label = line.split(',')[2]
        value = line.split(',')[3]

        if label == 'state':
            status = value
            break

    if status and status == 'not_created':
        display_message('Booting a vagrant VM...')
        local('vagrant up')

    config = ssh_config(name)

    extra_args = settings_dict(config)
    env.update(extra_args)

    env.site_path = '/vagrant'
    env.venv_path = '/opt/publet/venvs/publet'
    env.settings_file = 'settings_vagrant'
    env.bower_dir = os.path.join(env.site_path, 'publet/static')

    env.remote = 'vagrant'


@task
def fusion(name=''):
    env.site_path = '/vagrant'
    env.venv_path = '/opt/publet/venvs/publet'
    env.jar_path = '/opt/publet/jars'
    env.bin_path = '/opt/publet/bin'
    env.settings_file = 'settings_fusion'
    env.bower_dir = os.path.join(env.site_path, 'publet/static')

    env.remote = 'vagrant'

    env.username = 'vagrant'
    env.password = 'vagrant'
    env.host = FUSION_IP
    env.port = 22
    env.host_string = '%s@%s:%s' % (env.username, env.host, env.port)


@task
def vmless():
    env.is_vmless = True
    env.platform = platform.system()


# -----------------------------------------------------------------------------
# Tasks
# -----------------------------------------------------------------------------

@task
def provision():
    return sudo('salt-call --local state.highstate')


@task
def sync():
    upload_project_sudo('./pillar', '/srv')
    upload_project_sudo('./salt', '/srv')


@task
def sync_and_provision():
    sync()
    provision()
    sudo('service nginx restart')


@task
def install_saltstack():
    sudo('apt-get update')
    sudo('apt-get install -y software-properties-common')
    sudo('apt-get update')
    sudo('apt-get install -y salt-minion')


@task
def install_saltstack_from_git():
    sudo('/vagrant/bin/bootstrap-salt.sh -P git v2014.7')


@task
def bower_install(safe=True, path=None):
    if safe:
        assert_command_exists('bower')

    if path:
        with lcd(path):
            local('bower --config.analytics=false install')
    else:
        with cd(env.bower_dir):
            run('bower --config.analytics=false install')


@task
def local_bower_install():
    bower_install(safe=False, path='publet/static')


@task
def test():
    print env.is_vagrant
    local('ls')


@task
def link_salt():
    with settings(warn_only=True):
        sudo('ln -s /vagrant/pillar /srv/pillar')
        sudo('ln -s /vagrant/salt /srv/salt')


@task
def bootstrap(with_salt_from_git=False):
    """
    Prepare vagrant machine for work

    Install saltstack
    Symlink pillar and salt to the righ places
    Run saltstack
    Run usual Django commands
    """

    assert_command_exists('bower')

    display_message('Installing bower components...')
    bower_install(safe=False, path='publet/static')

    vagrant()

    display_message('Installing saltstack...')

    if with_salt_from_git:
        install_saltstack_from_git()
    else:
        install_saltstack()

    link_salt()

    display_message('Running saltstack...')

    with settings(warn_only=True):
        res = provision()

    if env.is_vagrant and not res.succeeded:
        provision()

    # This is here to force a logout of the vagrant user so that they changed
    # group settings on that user can be applied.  Lol, unix.
    disconnect_all()

    bootstrap_python_bits()


@task
def bootstrap_python_bits():
    vagrant()

    create_virtualenv()
    upgrade_pip()
    install_requirements()

    with cd(env.site_path):
        display_message('Migrating the database...')
        run(managepy('migrate --noinput'))

        display_message('Creating the superuser...')
        run(managepy('createsuperuser'))

        display_message('Backfilling the API keys...')
        run(managepy('backfill_api_keys'))

        display_message('Loading data...')
        run(managepy('loaddata initial.json'))

    display_message('All done.')


@task
def push():
    with settings(warn_only=True):
        remote_result = local('git remote | grep %s' % env.remote)
        if not remote_result.succeeded:
            display_message('Adding local remote')
            d = (env.remote, env.username, env.host, env.port)
            local('git remote add %s ssh://%s@%s:%s/opt/publet/apps/publet' %
                  d)

    if not exists(os.path.join(env.site_path, '.git')):
        # Create an empty git repo
        display_message('Creating an empty repo on the server')
        with cd(env.site_path):
            run('git init')
            run('git config receive.denyCurrentBranch ignore')
            run('git config core.worktree %s' % env.site_path)

    if env.username == 'ci':
        local('git fetch --unshallow')

    display_message('Pushing to remote repo')
    local('git push %s %s' % (env.remote, env.branch))

    with cd(env.site_path):
        run('git checkout %s -f' % env.branch)
        run('git rev-parse HEAD > .current-commit')

    # git checkout -f changes the ownership and permissions of files in the
    # working copy so we need to change it back to deploy:deploy here
    with cd(env.apps_path):
        sudo('chown -R deploy:deploy publet')
        rmpyc()


@task
def hup_gunicorn():

    # TODO: HUP doesn't reread new pip requirements

    sudo('supervisorctl restart publet')

    return

    pid_path = os.path.join(env.site_path, '.gunicorn.pid')

    if not exists(pid_path):
        return

    sudo('kill -HUP `cat %s`' % pid_path)


@task
def reload_rq():
    sudo('supervisorctl restart rq')


@task
def reload_consumer():
    sudo('supervisorctl restart consumer')


@task
def minify_javascript():
    with cd(env.site_path):
        run('./bin/compile_js')


def gulp_task(task):
    with cd(env.site_path):
        run('gulp {}'.format(task))


@task
def purge_publication_cache():
    with cd(env.site_path):
        run('./bin/purge-publications-in-redis')


@task
def upload_track():
    args = (env.publications_bucket,
            'publet/static/js/track.bundle.js',)
    run(python('/opt/publet/apps/publet/bin/upload_file_to_s3.py %s %s' %
        args))


@task
def deploy(with_themes=False):
    # Prevent CI from deploying when a release is in place
    if env.username == 'ci' and release_in_place():
        return

    assert_correct_branch()
    reset_permissions()

    push()
    ensure_virtualenv()

    bower_install()

    with cd(env.site_path):
        sudo('npm install')
        gulp_task('templates')
        minify_javascript()
        upload_track()

        run(pip('install -r requirements.txt --exists-action w'))

        run(managepy('migrate --noinput'))
        run(managepy('ensure_pubs_have_themes'))

        if with_themes:
            run(managepy('rebuild_all_themes'))

        run(managepy('collectstatic --noinput --ignore cache'))
        run(managepy('loaddata initial'))
        run(managepy('mark_deploy'))

    purge_publication_cache()
    hup_gunicorn()
    reload_rq()
    reload_consumer()

    reset_permissions()
    send_slack_message(
        'Deployed branch {} to {}'.format(env.branch, env.remote))


@task
def prepare():
    """
    Prepare a server
    """

    if env.requires_ubuntu_user:
        # AWS hosts need to log in with the ubuntu user
        env.host_string = 'ubuntu@%s:22' % env.host
    else:
        env.host_string = 'root@%s:22' % env.host

    sync()
    set_hostname(env.host)
    install_saltstack()
    provision()

    if env.is_lb:
        return

    if env.is_varnish:
        return

    env.host_string = '%s@%s:%s' % (env.username, env.host, env.port)
    deploy()

    # TODO: Make sure the proper Django Site instance exists


@task
def create_virtualenv():
    run('virtualenv %s --no-site-packages' % env.venv_path)


@task
def upgrade_pip():
    run(pip('install -U pip'))


@task
def install_requirements():
    with cd(env.site_path):
        run(pip('install --timeout=120 -r requirements.txt'
                ' --exists-action w'))


@task
def compress_file(src, dest):
    src_path, src_name = os.path.split(src)
    sudo('tar -czf %s -C %s %s' % (dest, src_path, src_name))


@task
def decompress_file(src, use_sudo=True):
    src_path, src_name = os.path.split(src)

    if env.is_vmless:
        cmd = local
        src = src_name
    else:
        cmd = sudo if use_sudo else run

    c = lcd if env.is_vmless else cd

    with c(src_path):
        cmd('tar -xzf %s' % src)


@task
def dump_db():
    date = get_current_datetime()

    backups_dir = '/tmp/backups'
    as_user('postgres', 'mkdir -p %s' % backups_dir)

    path = os.path.join(backups_dir, 'pgdump-%s.sql' % date)
    tar_path = os.path.join(backups_dir, 'pgdump-%s.sql.tar' % date)

    as_user('postgres', 'pg_dump -U postgres publet > %s' % path)
    compress_file(path, tar_path)

    sudo('chown deploy:deploy %s' % path)

    return tar_path, path


@task
def load_db(path):
    fn = local if env.is_vmless else run

    if is_osx():
        lc = 'en_US'
    elif is_linux():
        lc = 'en_US.utf8'
    else:
        lc = ''

    if lc:
        lc = '--lc-collate="{}" --lc-ctype="{}"'.format(lc, lc)

    fn('dropdb -U postgres publet')
    fn('createdb '
       '--username="postgres" --encoding="UTF8" '
       '--template="template0" {} publet'.format(lc))
    fn('psql -U postgres -d publet -f %s' % path)


@task
def load_latest_db():
    dumps_dir = 'db-dumps'
    dumps = os.listdir(dumps_dir)

    if not dumps:
        _die('cannot find db')

    dumps.reverse()
    latest = dumps[0]

    vagrant()

    remote_path = os.path.join(os.path.join('/vagrant', dumps_dir),
                               os.path.basename(latest))
    decompress_file(remote_path, use_sudo=False)
    load_db(os.path.join('/vagrant', dumps_dir, latest.replace('.tar', '')))


@task
def copy_db_from_a_to_b_abstract(source_env_fn, dest_env_fn, username):
    source_env_fn(username)
    tar_filename, filename = dump_db()

    local('mkdir -p db-dumps')

    basename = os.path.basename(tar_filename)
    local_db_path = os.path.join('db-dumps', basename)

    get(tar_filename, local_db_path)
    # FIXME:
    # run('rm %s %s'.format(tar_filename, filename))

    dest_env_fn(username)

    backups_dir = '/tmp/backups'
    run('mkdir -p %s' % backups_dir)

    if env.is_vmless:
        remote_path = local_db_path
    else:
        remote_path = os.path.join(backups_dir, os.path.basename(tar_filename))
        put(local_db_path, remote_path)

    decompress_file(remote_path)

    if dest_env_fn.__name__ != 'vagrant':
        sudo('supervisorctl stop all')

    load_db(remote_path.replace('.tar', ''))

    if dest_env_fn.__name__ != 'vagrant':
        sudo('supervisorctl start all')

    if dest_env_fn.__name__ == 'staging':
        domain = 'staging.publet.com'
    elif dest_env_fn.__name__ == 'vagrant':
        domain = 'publet.example.com'
    else:
        domain = ''

    if env.is_vmless:
        local(managepy('migrate --noinput'))
        local(managepy('loaddata initial.json'))
        local(managepy('set_site_domain {}'.format(domain)))
    else:
        with cd(env.site_path):
            run(managepy('migrate --noinput'))
            run(managepy('loaddata initial.json'))
            run(managepy('set_site_domain {}'.format(domain)))

            purge_publication_cache()

    if dest_env_fn.__name__ == 'staging':
        send_slack_message('Copied db from beta to staging.')


@task
def copy_beta_db_to_staging(username):
    copy_db_from_a_to_b_abstract(beta, staging, username)


@task
def copy_beta_db_to_local(username):
    copy_db_from_a_to_b_abstract(beta, vagrant, username)


@task
def copy_staging_db_to_local(username):
    copy_db_from_a_to_b_abstract(staging, vagrant, username)


@task
def move_publication_from_staging_to_beta(username, pk):
    staging(username)

    json_file = 'pub-%s.json' % pk
    json_path = '/tmp/%s' % json_file

    with cd(env.site_path):
        cmd = 'manage.py dumppub %s > %s --settings=publet.%s' % (
            pk, json_path, env.settings_file)
        run(python(cmd))

        get(json_path, json_file)

    beta(username)

    put(json_file, json_path)

    with cd(env.site_path):
        path = 'sql/reset-sequence-projects.sql'
        run('psql -U postgres -d publet -f %s' % path)

        run(python('manage.py loadpub %s --settings=publet.%s' % (
            json_path, env.settings_file)))


@task
def backup_db():
    filename = dump_db()

    args = ('publet-postgres-backups', filename,)
    run(python('/opt/publet/apps/publet/bin/upload_file_to_s3.py %s %s' %
        args))


@task
def reset_permissions():
    sudo('chown -R deploy:deploy /opt/publet')
    sudo('chmod -R 775 /opt/publet/apps/publet/publet/static')
    sudo('chmod -R 775 /opt/publet/static')


@task
def send_slack_message(text):
    if env.username:
        text += ' [by {}]'.format(env.username)

    payload = json.dumps(dict(text=text, username='publet-bot'))
    requests.post('https://hooks.slack.com/services/'
                  'T02UJ1S3F/B030R1K2L/oLpYq07ybAokzbZAS63UwQDu',
                  data=payload)


@task
def enable_maintenance(env):
    sudo('rm /etc/nginx/sites-enabled/{}'.format(env))
    sudo('ln -s /etc/nginx/sites-available/maintenance-{} '
         '/etc/nginx/sites-enabled/maintenance-{}'.format(env, env))

    sudo('/etc/init.d/nginx reload')
    send_slack_message('Maintenance enabled for {}'.format(env))


@task
def disable_maintenance(env):
    sudo('rm /etc/nginx/sites-enabled/maintenance-{}'.format(env))
    sudo('ln -s /etc/nginx/sites-available/{} '
         '/etc/nginx/sites-enabled/{}'.format(env, env))

    sudo('/etc/init.d/nginx reload')
    send_slack_message('Maintenance disabled for {}'.format(env))


@task
def collect_all_analytics():
    with cd(env.site_path):
        run(managepy('collect_all_analytics'))


@task
def test_access():
    run('echo hello')


@task
def pep8():
    assert_command_exists('pep8', msg='Please install pip requirements.  '
                                      'pip install -r requirements.txt')

    cmd = ('find . -type f -name "*.py" | '
           'grep -v migrations | grep -v trigger | grep -v settings | '
           'xargs pep8')

    with settings(warn_only=True):
        result = local(cmd)

    yiss = """
    __   _____ ____ ____  _ _ _
    \ \ / /_ _/ ___/ ___|| | | |
     \ V / | |\___ \___ \| | | |
      | |  | | ___) |__) |_|_|_|
      |_| |___|____/____/(_|_|_)
    """

    nope = """
      _   _  ___  ____  _____
     | \ | |/ _ \|  _ \| ____|
     |  \| | | | | |_) |  _|
     | |\  | |_| |  __/| |___
     |_| \_|\___/|_|   |_____|
     """

    if result.succeeded:
        print cyan(yiss)
    else:
        sys.stderr.write(red(nope))


@task
def find_tabs():
    local('./bin/find_tabs')


@task
def jshint():
    local('jshint publet/static/js')


@task
def build_chrome():
    cmd = '{} --pack-extension=chrome --pack-extension-key=chrome.pem'
    local(cmd.format(CHROME_PATH))


@task
def pm(cmd):
    """
    e.g. $ fab staging:honza pm:migrate
    """
    with cd(env.site_path):
        run(managepy(cmd))


@task
def remove_sass_cache():
    with cd(env.site_path):
        run('find . -type d -name ".sass-cache" -print0 | '
            'xargs -0 sudo rm -rf --')


@task
def rebuild_all_themes():
    remove_sass_cache()
    reset_permissions()

    with cd(env.site_path):
        run(managepy('rebuild_all_themes'))
        run(managepy('collectstatic --noinput'))

    purge_publication_cache()


@task
def rebuild_theme(theme):
    remove_sass_cache()
    reset_permissions()

    with cd(env.site_path):
        run(managepy('rebuild_all_themes {}'.format(theme)))
        run(managepy('collectstatic --noinput'))

    purge_publication_cache()


@task
def rebuild_all_screenshots():
    reset_permissions()

    with cd(env.site_path):
        run(managepy('rebuild_all_screenshots'))
        run(managepy('collectstatic --noinput'))


@task
def migrate_from_south():
    """
    Take a pg dump from a south-based app and convert to django 1.7

    This involves faking initial migrations and then migrating the rest
    for real
    """
    with cd(env.site_path):
        run(managepy('migrate --noinput --fake analytics 0001_initial'))
        run(managepy('migrate --noinput --fake fonts 0001_initial'))
        run(managepy('migrate --noinput --fake groups 0001_initial'))
        run(managepy('migrate --noinput --fake payments 0001_initial'))
        run(managepy('migrate --noinput --fake projects 0001_initial'))
        run(managepy('migrate --noinput --fake utils 0001_initial'))
        run(managepy('migrate --noinput'))


def get_remote_branch():
    with cd(env.site_path):
        branch = run('git rev-parse --abbrev-ref HEAD')

    return branch


@task
def load_geo_sql_file(path):
    remote_path = os.path.join('/tmp', os.path.basename(path))
    put(path, remote_path)

    with settings(hide('stdout'), warn_only=True):
        run('createdb -U postgres geo')

    with cd('/tmp'):
        run('tar -xzf {}'.format(remote_path))
        run('psql -U postgres -d geo -f {}'.format(remote_path[:-7]))


def _deploy_jar(name):
    with lcd(name):
        local('lein uberjar')

    local_jar_path = '{}/target/{}-0.1.0-SNAPSHOT-standalone.jar'.format(
        name, name)
    remote_jar_path = os.path.join(
        env.jar_path, '{}-0.1.0-SNAPSHOT-standalone.jar'.format(name))

    put(local_jar_path, remote_jar_path)

    sudo('supervisorctl restart {}'.format(name))
    send_slack_message('Deployed {} to {}'.format(name, env.remote))


@task
def deploy_track():
    _deploy_jar('track')


@task
def deploy_insights():
    _deploy_jar('insights')


@task
def deploy_presence():
    _deploy_jar('presence')


def rmpyc():
    """
    Remove .pyc files
    """
    run('find publet -type f -name "*.pyc" -print0 | xargs -0 rm -rf --')


@task
def rebuild_publications():
    with cd(env.site_path):
        run(managepy('rebuild_all_new_publications'))

    m = 'Rebuild of all publications scheduled on {}'.format(env.remote)
    send_slack_message(m)


@task
def merge_closeio():
    key = 'fe924e84bf63a5ee44aaa069873840bed0497e1480aee9c40e2cb681'
    c = './bin/merge_closeio.py --api-key {} --confirmed'.format(key)
    local(c)


@task
def restart_nginx():
    sudo('service nginx restart')


@task
def add_test_data(publication_id, num):
    with cd(env.site_path):
        run(managepy('add_test_data {} {}'.format(publication_id, num)))
