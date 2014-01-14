"""
Git related utilities.
======================

"""
import os
from fabric.api import fastprint, run, cd, task, env
from fabric.colors import red, cyan, green
from fabric.contrib.files import exists
import fabtools

from .common import setup_env


@task
def update_git_checkout(code_path, url, repo_alias, branch='master', tag=None):
    """Make sure there is a read only git checkout.

    :param code_path: Path to where the repo should be checked out.
    :type code_path: str

    :param url: Complete http url for cloning/checking out the repo.
    :type url: str

    :param repo_alias: Alias name under which the repo should be checked out.
    :type repo_alias: str

    :param branch: The name of the branch to build from. Defaults to 'master'.
    :type branch: str

    :param tag: Tag to checkout. If None this is ignored. If not none will be
        used in preference to branch.
    :type tag: None, str

    To run e.g.::

        fab -H foo:1234 remote update_git_checkout

    """
    fastprint(cyan('Updating git checkout.\n'))
    fastprint(cyan('code_path: %s\n' % code_path))
    fastprint(cyan('url: %s\n' % url))
    fastprint(cyan('repo_alias: %s\n' % repo_alias))
    fastprint(cyan('branch: %s\n' % branch))
    fastprint(cyan('tag: %s\n' % tag))
    setup_env()
    repo_path = os.path.join(code_path, repo_alias)

    fabtools.require.deb.package('git')
    if not exists(repo_path):
        fastprint(green('Repository does not exist, creating.\n'))
        fabtools.require.directory(code_path, use_sudo=True, owner=env.user)
        with cd(code_path):
            run('git clone %s %s' % (url, repo_alias))
    else:
        fastprint(green('Repo checkout does exist, updating.'))
        with cd(repo_path):
            # Get any updates first
            run('git fetch')
            if tag is not None:
                tags = run('git tag --list')
                if tag in tags:
                    fastprint(green('Checking out tag.'))
                    run('git checkout %s' % tag)
                else:
                    fastprint(red('Checking out tag failed - unknown tag.'))
                    raise Exception('Git checkout failed for tag')

            elif branch != 'master':
                fastprint(green('Checking out branch.'))
                branches = run('git branch')
                if branch not in branches:
                    print branches
                    run('git branch --track %s origin/%s' % (branch, branch))
                if ('* %s' % branch) not in branches:
                    run('git checkout %s' % branch)
            else:
                fastprint(green('Checking out master.'))
                run('git checkout master')
            run('git pull')
    fastprint(green('Checking out tag completed.'))


@task
def remove_local_branches(code_path):
    """Remove any local branches you may have in your repo - use with caution!

    Any local changes will be dropped. Master will be checked out and all
    other local branches removed.

    :param code_path: Path to where the repo should be.
    :type code_path: str

    .. versionadded:: 0.16.0
    """
    fastprint(red('Removing all local branches from repo! %s\n' % code_path))
    with cd(code_path):
        # Get rid of any local changes
        run('git reset --hard')
        # Get back onto master branch
        run('git checkout master')
        # Delete all local branches
        run('git branch | grep -v \* | xargs git branch -D')
