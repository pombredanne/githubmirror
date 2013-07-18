# -*- encoding: utf-8 -*-

import os
import sys
import git
import json
import github


def setup_config_file(workdir):
    config = dict()
    with open(get_workdir_path('.githubmirror', workdir), 'w') as config_file:
        prompt = ("Please give me a Github API token, "
                  "create on https://github.com/settings/applications : ")
        auth_token = raw_input(prompt)
        config = dict(auth_token=auth_token)
        json.dump(config, config_file)
    return config


def get_config_file(workdir):
    if not os.path.isfile(get_workdir_path('.githubmirror', workdir)):
        setup_config_file(workdir)

    with file(get_workdir_path('.githubmirror', workdir)) as f:
        try:
            config = json.load(f)
        except ValueError:
            return setup_config_file(workdir)
        return config


def get_auth_token(workdir):
    config = get_config_file(workdir)
    return config.get('auth_token')


def get_github_client(workdir):
    token = get_auth_token(workdir)
    return github.Github(token)


def get_organization(organization_name, workdir):
    gh = get_github_client(workdir)
    org = None
    while not org:
        try:
            org = gh.get_organization(organization_name)
        except github.GithubException as e:
            print >>sys.stderr, "Github error: %s" % e
            setup_config_file(workdir)
    return org


class FetchProgress(git.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        # Ignore the details, just give an indication that we haven't hung:
        sys.stdout.write(".")
        sys.stdout.flush()


def expand_workdir(workdir):
    return os.path.expanduser(os.path.expandvars(workdir))


def get_workdir_path(filename, workdir):
    return os.path.join(expand_workdir(workdir), filename)


def get_repo_path(repo_name, workdir):
    return get_workdir_path("%s.git" % repo_name, workdir)


def init_repos(repos, workdir):
    remote_name = 'origin'
    for repo in repos:
        url = repo.ssh_url
        gitdir = git.Repo.init(get_repo_path(repo.name, workdir), bare=True)
        # Cleanup existing origin, if any
        try:
            remote = gitdir.remote(remote_name)
            gitdir.delete_remote(remote)
        except (ValueError, git.exc.GitCommandError):
            pass

        gitdir.git.remote("add", "--mirror", remote_name, url)


def fetch(repos, workdir):
    for repo in repos:
        path = get_repo_path(repo.name, workdir)
        gitdir = git.Repo.init(path, bare=True)
        remote = gitdir.remote(name='origin')
        print ("Fetching %s in %s..." % (repo.ssh_url, path)),  # to avoid newline
        remote.fetch(progress=FetchProgress())
        print ""
