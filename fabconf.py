import os

from fabric.api import task, env
from fabric.api import run, roles, cd, execute, hide, puts


# https://docs.gitea.io/en-us/install-from-binary/
# https://docs.gitea.io/en-us/backup-and-restore/


env.is_python3 = True
env.project_name = 'gitea'
env.sites = ('gitea', )
# env.repository = 'ssh://bnzk@gitea.bnzk.ch:61005/bnzk_internal/{project_name}.git'.format(**env)
env.repository = 'git@bitbucket.org:youruser/yourgitea.git'.format(**env)
env.remote_ref = 'origin/master'
# gitea version
env.requirements_file = 'gitea-version.txt'


# ==============================================================================
# Tasks which set up deployment environments
# ==============================================================================


@task
def live():
    """
    Use the live deployment environment.
    """
    env.env_prefix = 'live'
    env.main_user = 'youruser'.format(**env)
    server = '{main_user}@yourhost.com'.format(**env)
    env.roledefs = {
        'web': [server],
        'db': [server],
    }
    generic_env_settings()


@task
def stage():
    """
    Use the sandbox deployment environment on xy.bnzk.ch.
    """
    exit("no stage for gitea!")
    env.env_prefix = 'stage'
    env.main_user = '{project_name}'.format(**env)
    server = '{main_user}@yourhost.com'.format(**env)
    env.roledefs = {
        'web': [server],
        'db': [server],
    }
    generic_env_settings()


def generic_env_settings():
    if not getattr(env, 'deploy_crontab', None):
        env.deploy_crontab = False
    env.project_dir = '/home/{main_user}/{project_name}-{env_prefix}'.format(**env)
    env.restart_command = 'systemctl --user daemon-reload && systemctl --user restart {site}-{env_prefix}.service'
    # not needed with uwsgi emporer mode, cp is enough
    # env.uwsgi_restart_command = 'touch $HOME/uwsgi.d/{site}-{env_prefix}.ini'


live()
