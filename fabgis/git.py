"""Git related utilities."""
import os
from fabric.api import fastprint, run, cd
from fabric.colors import red, blue, green
from fabric.contrib.files import exists
import fabtools

from .common import setup_env


def update_git_checkout(code_path, url, repo_alias, branch='master', tag=None):
    """Make sure there is a read only git checkout.

    :param code_path: Path to where the repo should be.
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

        fab -H 188.40.123.80:8697 remote update_git_checkout

    """
    fastprint(blue('Updating git checkout.'))
    fastprint(blue('code_path: %s' % code_path))
    fastprint(blue('url: %s' % url))
    fastprint(blue('repo_alias: %s' % repo_alias))
    fastprint(blue('branch: %s' % branch))
    fastprint(blue('tag: %s' % tag))
    setup_env()
    repo_path = os.path.join(code_path, repo_alias)

    fabtools.require.deb.package('git')
    if not exists(repo_path):
        fastprint(green('Basic Repository does not exist, creating.'))
        run('mkdir -p %s' % code_path)
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
