from github.GithubObject import NotSet, is_undefined

from models.gh import OrganizerOrganization, OrganizerRepository
from services.github import gh


def update_repository_settings(org_name, repo_name):
    print(f"Updating the settings of repository {org_name}/{repo_name}")
    org = OrganizerOrganization(gh.get_organization(org_name))
    repo = org.get_repository(repo_name)
    repo.update_settings()


def update_repository_labels(org_name, repo_name):
    print(f"Updating the labels of repository {org_name}/{repo_name}")
    org = OrganizerOrganization(gh.get_organization(org_name))
    repo = org.get_repository(repo_name)
    repo.update_labels()


def update_repository_security_settings(org_name, repo_name):
    print(f"Updating the security settings of repository {org_name}/{repo_name}")
    org = OrganizerOrganization(gh.get_organization(org_name))
    repo = org.get_repository(repo_name)
    repo.update_security_scanning()


def update_repo_branch_protection(org: OrganizerOrganization, repo_name: str):
    print(
        f"Updating the branch protection settings of repository {org.name}/{repo_name}"
    )
    repo = org.get_repository(repo_name)
    update_repo_branch_protection(repo)


def update_repo_branch_protection(repo: OrganizerRepository):
    settings = repo.get_organizer_settings()
    if "branches" not in settings:
        return
    for branch in settings["branches"]:
        update_branch_protection(repo, branch)


def update_branch_protection(repo: OrganizerRepository, branch_name: str):
    if "branches" not in repo._settings:
        return
    if branch_name not in repo._settings["branches"]:
        return
    print(
        f"Updating branch protection for {branch_name} in {repo.organization.login}/{repo.name}."
    )
    bsettings = repo._settings["branches"][branch_name]
    branch = repo.repository.get_branch(branch_name)
    repo.branch_protection(
        branch=branch,
        required_status_checks=bsettings.get("required_status_checks", NotSet),
        enforce_admins=bsettings.get("enforce_admins", NotSet),
        require_review=bsettings.get("require_review", True),
        restrictions=bsettings.get("restrictions", {}),
        required_linear_history=bsettings.get("required_linear_history", NotSet),
        allow_force_pushes=bsettings.get("allow_force_pushes", NotSet),
        required_approving_review_count=bsettings.get(
            "required_approving_review_count", 1
        ),
        require_code_owner_reviews=bsettings.get("require_code_owner_reviews", NotSet),
        dismiss_stale_reviews=bsettings.get("dismiss_stale_reviews", NotSet),
        dismissal_restrictions=bsettings.get("dismissal_restrictions", {}),
        bypass_restrictions=bsettings.get("bypass_restrictions", {}),
        lock_branch=bsettings.get("lock_branch", NotSet),
        allow_fork_syncing=bsettings.get("allow_fork_syncing", NotSet),
        block_creations=bsettings.get("block_creations", NotSet),
        required_conversation_resolution=bsettings.get(
            "required_conversation_resolution", NotSet
        ),
        allow_deletions=bsettings.get("allow_deletions", False),
    )


def update_repository_default_branch(org: OrganizerOrganization, repo_name: str):
    print(f"Updating the default branch settings of repository {org.name}/{repo_name}")
    repo = org.get_repository(repo_name)
    repo.update_default_branch()
