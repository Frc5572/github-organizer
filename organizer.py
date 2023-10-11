import os
import random
import string

import click
import yaml

from models.gh import OrganizerOrganization

# import models.gh
# import tasks.github
from services.github import gh
from services.tasks import (
    update_repo_branch_protection,
    update_repository_default_branch,
    update_repository_labels,
    update_repository_security_settings,
    update_repository_settings,
)

CONFIG = None


@click.group()
@click.option(
    "-c",
    "--config",
    type=click.Path(),
    help="Local configuration instead of organizational config",
)
@click.pass_context
def cli(ctx, config):
    if ctx.parent:
        print(ctx.parent.get_help())
    if config:
        with open("config.yml", "r") as file:
            CONFIG = yaml.safe_load(file)


@cli.command(short_help="List the settings for an organization or repository")
@click.argument("organization")
@click.argument("repository", required=False)
def settings(organization, repository):
    org = OrganizerOrganization(gh.get_organization(organization))
    if repository:
        repo = org.get_repository(repository)
        click.echo(f"Organizer Settings for: {org.login}/{repo.name}")
        click.echo(yaml.dump(repo.get_organizer_settings(), default_flow_style=False))
    else:
        click.echo(f"Organizer Settings for: {org.name} ({org.login})")
        click.echo(yaml.dump(org.configuration, default_flow_style=False))
    # print(repo.name)


@cli.command(short_help="Update a single repository's settings")
@click.argument("organization")
@click.argument("repository")
def update_repo(organization, repository):
    update_repository_settings(organization, repository)
    update_repository_labels(organization, repository)
    update_repository_security_settings(organization, repository)


# @cli.command(short_help="Update all repositories in an organization")
# @click.argument('organization')
# def update_repos(organization):
#     tasks.github.update_organization_settings(organization, True)


# @cli.command(short_help="Update repository teams for an organization")
# @click.argument('organization')
# def update_team_repos(organization):
#     tasks.github.update_organization_teams(organization)


# @cli.command(short_help="Update repository teams for an organization")
# @click.argument('organization')
# @click.argument('team')
# def get_team_permissions(organization, team):
#     installation = ghapp.get_org_installation(organization)
#     gh = get_organization_client(organization)
#     org = models.gh.Organization(gh, organization)
#     team = org.get_team_by_name(team)
#     click.echo(models.gh.team_has_repositories(installation, team))


@cli.command(short_help="List the repositories in an organization")
@click.argument("organization")
def list_repos(organization):
    org = OrganizerOrganization(gh.get_organization(organization))
    for repo in org.get_repositories():
        click.echo(repo.name)


# @cli.command(short_help="")
# @click.argument('organization')
# def list_org_projects(organization):
#     gh = get_organization_client(organization)
#     org = models.gh.Organization(gh, organization)
#     for project in org.get_projects():
#         click.echo('%s\t%s' % (project.id, project.name))


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('project')
# def get_org_project(organization, project):
#     gh = get_organization_client(organization)
#     org = models.gh.Organization(gh, organization)
#     ghproject = org.get_project_by_name(project)
#     click.echo('%s\t%s' % (ghproject.id, ghproject.name))


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('project')
# @click.argument('column')
# def get_org_project_column(organization, project, column):
#     gh = get_organization_client(organization)
#     org = models.gh.Organization(gh, organization)
#     project = org.get_project_by_name(project)
#     column = project.get_column_by_name(column)
#     click.echo('%s\t%s' % (column.id, column.name))


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('repository')
# @click.argument('project')
# def get_repo_project(organization, repository, project):
#     gh = get_organization_client(organization)
#     org = models.gh.Organization(gh, organization)
#     repo = org.get_repository(repository)
#     ghproject = repo.get_project_by_name(pupdate_repo_branch_protectionroject)
#     click.echo('%s\t%s' % (ghproject.id, ghproject.name))


@cli.command(
    short_help="Update the branch protection settings for an entire org or single repository"
)
@click.argument("organization")
@click.argument("repository", required=False)
def update_branch_protection(organization, repository):
    org = OrganizerOrganization(gh.get_organization(organization))
    if repository:
        update_repo_branch_protection(org, repository)
    else:
        for repo in org.get_repositories():
            update_repo_branch_protection(repo)


@cli.command(
    short_help="Update the default branch settings for an entire org or single repository"
)
@click.argument("organization")
@click.argument("repository", required=False)
def default_branch(organization, repository):
    org = OrganizerOrganization(gh.get_organization(organization))
    if repository:
        update_repository_default_branch(org, repository)
    # else:
    #     for repo in org.get_repositories():
    #         update_repository_default_branch(repo)


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('repository')
# @click.argument('issue')
# def assign_issue(organization, repository, issue):
#     tasks.github.assign_issue(organization, repository, issue)


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('repository')
# @click.argument('issue')
# def label_issue(organization, repository, issue):
#     tasks.github.label_issue(organization, repository, issue)


# @cli.command(short_help="")
# @click.argument('organization')
# @click.argument('team')
# def update_team_membership(organization, team):
#     tasks.github.update_team_members(organization, team)


# @cli.command(short_help="")
# @click.argument('organization')
# def update_org_team_membership(organization):
#     tasks.github.update_organization_team_members(organization, synchronous=True)


# @cli.command(short_help="")
# def app_info():
#     for install_id in ghapp.get_installations():
#         click.echo('Install ID: %s' % (install_id))
#         install = ghapp.get_installation(install_id)
#         click.echo(install.get_organization())


# @cli.command(short_help="")
# @click.argument('organization')
# def org_info(organization):
#     click.echo(ghapp.get_org_installation(organization))


if __name__ == "__main__":
    cli()
