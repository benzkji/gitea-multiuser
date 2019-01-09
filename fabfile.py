import datetime
import sys

from fabric.api import task, run, roles, cd, execute, hide, puts

from fabconf import env, stage, live  # noqa


# hm. https://github.com/fabric/fabric/issues/256
sys.path.insert(0, sys.path[0])

# set some basic things, that are just needed.
env.forward_agent = True


@task
@roles('web', 'db')
def clone_repos():
    """
    clone the repository.
    """
    with hide('running', 'stdout'):
        exists = run('if [ -d "{project_dir}" ]; then echo 1; fi'.format(**env))
    if exists:
        puts('Assuming {repository} has already been cloned since '
             '{project_dir} exists.'.format(**env))
        return
    run('git clone {repository} {project_dir}'.format(**env))
    with cd(env.project_dir):
        run('git submodule update --init'.format(**env))
    puts('cloned {repository} to {project_dir}.'.format(**env))


@task
@roles('web', 'db')
def bootstrap():
    clone_repos()
    puts('Bootstrapped {project_name} on {host} (cloned repos).'.format(**env))


@task
def deploy(verbosity='noisy'):
    """
    Full server deploy.
    Updates the repository (server-side), synchronizes the database, collects
    static files and then restarts the web service.
    """
    if verbosity == 'noisy':
        hide_args = []
    else:
        hide_args = ['running', 'stdout']
    with hide(*hide_args):
        puts('Updating repository...')
        execute(update)
        puts('Restarting systemd service...')
        execute(restart)


@task
@roles('web', 'db')
def update(action='check', tag=None):
    """
    Update the repository (server-side).
    """
    with cd(env.project_dir):
        old_gitea_version = run('cat gitea-version.txt')
        remote, dest_branch = env.remote_ref.split('/', 1)
        run('git fetch {remote}'.format(remote=remote,
                                        dest_branch=dest_branch, **env))
        with hide('running', 'stdout'):
            changed_files = run('git diff-index --cached --name-only '
                                '{remote_ref}'.format(**env)).splitlines()
        if not changed_files and action != 'force':
            # No changes, we can exit now.
            return
        reqs_changed = False
        if action == 'check':
            if env.requirements_file in changed_files:
                reqs_changed = True
        # before. run('git merge {remote_ref}'.format(**env))
        if tag:
            run('git checkout tags/{tag}'.format(tag=tag, **env))
        else:
            run('git checkout {dest_branch}'.format(dest_branch=dest_branch, **env))
            run('git pull'.format(dest_branch=dest_branch, **env))
        run('find -name "*.pyc" -delete')
        # attention, here, adapt your .gitignore accordingly if you have other data...or comment this line.
        run('git clean -df')
        # run('git clean -df {project_name} docs requirements public/static '.format(**env))
        # fix_permissions()
    if action == 'force' or reqs_changed:
        execute(install_gitea_version)


@task
@roles('web')
def install_gitea_version():
    """
    install defined gitea version (in gitea-version.txt)
    """
    with cd(env.project_dir):
        new_gitea_version = run('cat gitea-version.txt')
        run('mv gitea gitea-backup-%s' % (datetime.datetime.now().strftime('%Y-%d-%m--%H-%M-%S')))
        run('wget -O gitea https://dl.gitea.io/gitea/{new_version}/gitea-{new_version}-linux-amd64'
            .format(**{'new_version': new_gitea_version}))
        run('chmod +x gitea')
        # not working for now!
        # was done before, on server
        # run('gpg --keyserver pgp.mit.edu --recv 7C9E68152594688862D62AF62D9AE806EC1592E2')
        # run('wget -O https://dl.gitea.io/gitea/{new_version}/gitea-{new_version}-linux-amd64.asc'
        #     .format(**{'new_version': new_gitea_version}))
        # run('gpg --verify gitea-%S-linux-amd64.asc gitea' % new_gitea_version)


@task
@roles('web')
def restart():
    """
    install and restart systemd service
    """
    if env.is_nginx_gunicorn:
        copy_restart_gunicorn()
        copy_restart_nginx()


def stop_gunicorn():
    for site in env.sites:
        run(env.gunicorn_stop_command.format(site=site, **env))


def copy_restart_gunicorn():
    for site in env.sites:
        if env.get('is_systemd', None):
            run(
                'cp {project_dir}/systemd/{site}-{env_prefix}.service'
                ' $HOME/.config/systemd/user/.'.format(site=site, **env)
            )
        else:
            run(
                'cp {project_dir}/deployment/gunicorn/{site}-{env_prefix}.sh'
                ' $HOME/init/.'.format(site=site, **env)
            )
            run('chmod u+x $HOME/init/{site}-{env_prefix}.sh'.format(site=site, **env))
        run(env.gunicorn_restart_command.format(site=site, **env))


def copy_restart_nginx():
    # not needed, all in gitea binary!
    pass


def copy_restart_uwsgi():
    for site in env.sites:
        run(
            'cp {project_dir}/deployment/uwsgi/{site}-{env_prefix}.ini'
            ' $HOME/uwsgi.d/.'.format(site=site, **env)
        )
        # cp does the touch already!
        # run(env.uwsgi_restart_command.format(site=site, **env))


@task
@roles('web')
def get_version():
    """
    Get installed version from each server.
    """
    with cd(env.project_dir):
        run('git describe --tags')
        run('git log --graph --pretty=oneline -n20')
