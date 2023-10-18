"""Models for Organizer"""
from copy import copy

import yaml
from github import Branch, NamedUser, Organization, Repository, Team
from github.GithubException import GithubException
from github.GithubObject import NotSet

DEFAULT_LABEL_COLOR = "000000"
CACHE_SHORT = 5 * 60  # Five minutes
CACHE_MEDIUM = 60 * 60  # One hour
CACHE_LONG = 24 * 60 * 60  # One day
GLOBAL_CONFIG = None


def update_global_config(config: dict):
    """Update the global config when using a local file"""
    global GLOBAL_CONFIG  # pylint: disable=global-statement
    GLOBAL_CONFIG = config


# def issue_has_projects(installation, organization, repository, issue):
#     query = """
#     {
#       repository(owner:"%s", name:"%s") {
#         issue(number:%s) {
#           projectCards (archivedStates: NOT_ARCHIVED, first: 1) {
#             edges {
#               node {
#                 id
#               }
#             }
#           }
#         }
#       }
#     }
#     """ % (
#         organization,
#         repository,
#         issue,
#     )
#     results = installation.graphql({"query": query})
#     return len(results["data"]["repository"]["issue"]["projectCards"]["edges"]) > 0


# def team_has_repositories(installation, team):
#     # GET /teams/:team_id/repos
#     results = installation.rest(
#         "get",
#         "teams/%s/repos" % (team.id),
#         payload=False,
#         accepts=["application/vnd.github.hellcat-preview+json"],
#     )
#     repositories = {}
#     for repo in results:
#         repositories[repo["name"]] = []
#         for permission in repo["permissions"]:
#             if repo["permissions"][permission]:
#                 repositories[repo["name"]].append(permission)
#     return repositories


class OrganizerOrganization:
    """Class to represent a Github Organization"""

    configuration = None

    def __repr__(self):
        return "OrganizerOrganization %s" % self.name

    def __str__(self):
        return self.__repr__()

    def __init__(self, organization: Organization):
        """Initialize Class"""
        self.org = organization
        self.configuration = self.get_configuration()
        self.name = organization.name
        self.login = organization.login

    def get_repository(self, name: str):
        """Get a specific repository from the organization"""
        try:
            repo = self.org.get_repo(name)
            return OrganizerRepository(self, repo)
        except Exception:
            return None

    def get_configuration(self):
        """Get the configuration for the organization"""
        if GLOBAL_CONFIG is not None:
            self.configuration = GLOBAL_CONFIG
            return GLOBAL_CONFIG
        if self.configuration is not None:
            return self.configuration
        try:
            config_repository = self.org.get_repo(".github")
            return yaml.safe_load(
                config_repository.get_contents("organizer.yaml").decoded_content
            )
        except Exception:
            try:
                config_repository = self.org.get_repo(".github")
                return yaml.safe_load(
                    config_repository.get_contents("organizer.yaml").decoded_content
                )
            except Exception:
                return False

    def get_repositories(self):
        """Get all repositories for the organizations"""
        for repository in self.org.get_repos():
            if "exclude_repositories" in self.configuration:
                if repository.name in self.configuration["exclude_repositories"]:
                    continue
            if self.configuration.get("exclude_forks", False) and repository.fork:
                continue
            if (
                self.configuration.get("exclude_archived", False)
                and repository.archived
            ):
                continue
            yield OrganizerRepository(self, repository)

    def get_team(self, team_name) -> list:
        """Get a specific team"""
        try:
            team = self.org.get_team_by_slug(team_name)
            return OrganizerTeam(self, team)
        except Exception:
            return None

    def get_teams(self):
        """Get all teams in an org"""
        teams = []
        for team in self.org.get_teams():
            teams.append(OrganizerTeam(self, team))
        return teams

    def get_teams_members(self):
        """Get all members of all teams in an org"""
        teams = []
        for team in self.get_teams():
            teams.append(
                {
                    "team": team.name,
                    "members": [
                        {"name": x.name, "login": x.login} for x in team.get_members()
                    ],
                }
            )
        return teams

    def update_team(self, team_name: str, team_data: dict):
        """Update single team within organization"""
        team = None
        try:
            team = self.org.get_team_by_slug(team_name)
            team.edit(
                name=team_name,
                description=team_data.get("description", NotSet),
                privacy=team_data.get("privacy", NotSet),
            )
        except Exception:
            team = self.org.create_team(
                name=team_name,
                description=team_data.get("description", NotSet),
                privacy=team_data.get("privacy", NotSet),
            )
        oteam = OrganizerTeam(self, team)
        oteam.update_members()

    def update_teams(self) -> None:
        """Update all teams in the organization"""
        if "teams" not in self.configuration or not isinstance(
            self.configuration["teams"], dict
        ):
            return None
        for team_name, data in self.configuration["teams"].items():
            self.update_team(team_name=team_name, team_data=data)


class OrganizerRepository:
    """Class representing a GitHub Repository"""

    def __repr__(self):
        return "OrganizerRepository %s/%s" % (self.organization.name, self.name)

    def __str__(self):
        return self.__repr__()

    def __init__(self, org: OrganizerOrganization, repo: Repository):
        """Inigtialize Class"""
        self.organization = org
        self.repository = repo
        self.name = repo.name
        self._settings = None

    def update_settings(self):
        """Update General repositiroy settings"""
        organizer_settings = self.get_organizer_settings()
        self.repository.edit(
            has_issues=organizer_settings.get("features", {}).get("has_issues", NotSet),
            has_projects=organizer_settings.get("features", {}).get(
                "has_projects", NotSet
            ),
            has_wiki=organizer_settings.get("features", {}).get("has_wiki", NotSet),
            allow_forking=organizer_settings.get("features", {}).get(
                "allow_forking", NotSet
            ),
            web_commit_signoff_required=organizer_settings.get("features", {}).get(
                "web_commit_signoff_required", NotSet
            ),
            # has_downloads = organizer_settings.get('features', {}).get('has_downloads', NotSet),
            allow_squash_merge=organizer_settings.get("merges", {}).get(
                "allow_squash_merge", NotSet
            ),
            allow_merge_commit=organizer_settings.get("merges", {}).get(
                "allow_merge_commit", NotSet
            ),
            allow_rebase_merge=organizer_settings.get("merges", {}).get(
                "allow_rebase_merge", NotSet
            ),
            allow_auto_merge=organizer_settings.get("merges", {}).get(
                "allow_auto_merge", NotSet
            ),
            delete_branch_on_merge=organizer_settings.get("merges", {}).get(
                "delete_branch_on_merge", NotSet
            ),
            allow_update_branch=organizer_settings.get("merges", {}).get(
                "allow_update_branch", NotSet
            ),
            use_squash_pr_title_as_default=organizer_settings.get("merges", {}).get(
                "use_squash_pr_title_as_default", NotSet
            ),
            squash_merge_commit_title=organizer_settings.get("merges", {}).get(
                "squash_merge_commit_title", NotSet
            ),
            squash_merge_commit_message=organizer_settings.get("merges", {}).get(
                "squash_merge_commit_message", NotSet
            ),
            merge_commit_title=organizer_settings.get("merges", {}).get(
                "merge_commit_title", NotSet
            ),
            merge_commit_message=organizer_settings.get("merges", {}).get(
                "merge_commit_message", NotSet
            ),
        )

    def update_default_branch(self):
        """Update Default Branch for a repository"""
        org_settings = self.get_organizer_settings()
        if "branches" not in org_settings:
            return

        # If this repo is a fork then leave it alone.
        if self.repository.source:
            return

        for branch in org_settings["branches"]:
            settings = org_settings["branches"][branch]
            if "default" not in settings:
                continue
            if not settings["default"]:
                continue
            if self.repository.default_branch == branch:
                return

            # Fails if branch exists, creates it from current default branch otherwise.
            # Saves us at least one API call to see if the branch exists
            # try:
            #     self.create_branch(branch)
            # except:
            #     pass
            try:
                self.repository.edit(default_branch=branch)
            except Exception:
                pass

    def get_labels(self):
        """Get labels for a repository"""
        labels = {}
        for label in self.repository.get_labels():
            labels[label.name] = label
        return labels

    def get_topics(self):
        """Get topics for a repository"""
        return self.repository.get_topics()

    def get_organizer_settings(self, name=False, maxdepth=5):
        """Get organizaer settings for a repository"""
        if self._settings is not None:
            return self._settings
        topic_assignment = False
        if self.organization.configuration.get("topics_for_assignment", True):
            topics = self.get_topics()
            topic_assignments = [x for x in topics if x.startswith("gho-")]
            if len(topic_assignments) == 1:
                topic_assignment = topic_assignments[0][4:]

        if not self.organization.configuration:
            return False
        if "repositories" not in self.organization.configuration:
            # Convert from the old style configuration to the current version
            settings = copy(self.organization.configuration)
            settings["merges"] = {}
            settings["features"] = {}
            if "labels" in settings:
                del settings["labels"]
            for feature in ["has_issues", "has_wiki", "has_downloads", "has_projects"]:
                if feature in settings:
                    settings["features"][feature] = settings[feature]
                    del settings[feature]
            for merge in [
                "allow_rebase_merge",
                "allow_squash_merge",
                "allow_merge_commit",
            ]:
                if merge in settings:
                    settings["merges"][merge] = settings[merge]
                    del settings[merge]
            return settings
        if name and name in self.organization.configuration["repositories"]:
            settings = self.organization.configuration["repositories"][name]
        elif (
            topic_assignment
            and topic_assignment in self.organization.configuration["repositories"]
        ):
            settings = self.organization.configuration["repositories"][topic_assignment]
        elif not name and self.name in self.organization.configuration["repositories"]:
            settings = self.organization.configuration["repositories"][self.name]
        elif "default" in self.organization.configuration["repositories"]:
            settings = self.organization.configuration["repositories"]["default"]
        if not settings:
            return False

        if isinstance(settings, str):
            settings = {"extends": settings}

        if "extends" in settings and maxdepth > 0:
            parent = self.get_organizer_settings(
                name=settings["extends"], maxdepth=maxdepth - 1
            )
            if parent:
                parent.update(settings)
                settings = parent
            del settings["extends"]

        self._settings = settings
        return settings

    def update_labels(self):
        """Update labels for a repository"""
        current_labels = self.get_labels()  # [x.name for x in self.ghrep.labels()]

        # Remove any labels not in the configuration
        if self.organization.configuration.get("labels_clean", False):
            label_names = [
                x["name"] for x in self.organization.configuration.get("labels", [])
            ]
            for active_label in self.repository.get_labels():
                if active_label.name not in label_names:
                    active_label.delete()

        for config_label in self.organization.configuration.get("labels", []):
            if config_label.get("old_name"):
                label_object = self.repository.get_label(config_label["old_name"])
                if label_object:
                    label_object.edit(
                        config_label["name"],
                        config_label.get("color", DEFAULT_LABEL_COLOR),
                        config_label.get("description", NotSet),
                    )
                    continue

            if config_label["name"] in current_labels:
                label_object = current_labels[
                    config_label["name"]
                ]  # self.ghrep.label(config_label['name'])
                if not label_matches(config_label, label_object):
                    label_object.edit(
                        config_label["name"],
                        config_label.get("color", DEFAULT_LABEL_COLOR),
                        config_label.get("description", None),
                    )
            else:
                self.repository.create_label(
                    config_label["name"],
                    config_label.get("color", DEFAULT_LABEL_COLOR),
                    config_label.get("description", NotSet),
                )

    # def update_issues(self):
    #     organizer_settings = self.get_organizer_settings()
    #     if not organizer_settings:
    #         return False
    #     if "auto_assign_project" not in organizer_settings["issues"]:
    #         return False

    #     issue_config = organizer_settings["issues"]

    #     if "organization" in issue_config:
    #         project = self.organization.ghorg.project(issue_config["name"])
    #     else:
    #         project = self.ghrep.project(issue_config["name"])
    #     project_column = project.column(issue_config["column"])

    #     for issue in self.ghrep.issues(state="open", sort="created", direction="asc"):
    #         project_column.create_card_with_issue(issue)

    def update_security_scanning(self) -> None:
        """Update Security Scanning settings for a repository"""
        organizer_settings = self.get_organizer_settings()
        if organizer_settings and "dependency_security" not in organizer_settings:
            sec = organizer_settings["dependency_security"]
            if "alerts" in sec:
                self.toggle_vulnerability_alerts(sec["alerts"])
            if "automatic_fixes" in sec:
                self.toggle_security_fixes(sec["automatic_fixes"])

    def toggle_vulnerability_alerts(self, enable):
        """Update Vulnerability Alert settings for a repository"""
        if enable:
            self.repository.enable_vulnerability_alert()
        else:
            self.repository.disable_vulnerability_alert()

    def toggle_security_fixes(self, enable):
        """Update Security Fix settings for a repository"""
        if enable:
            self.repository.enable_automated_security_fixes()
        else:
            self.repository.disable_automated_security_fixes()

    # def get_projects(self):
    #     for project in self.ghrep.projects():
    #         yield Project(self.client, project, self.organization)

    # def get_project_by_name(self, name):
    #     def repo_get_project_id_from_name(repo, name):
    #         for project in repo.get_projects():
    #             if project.name == name:
    #                 return project.id
    #         return False

    #     id = repo_get_project_id_from_name(self, name)
    #     if not id:
    #         return False
    #     return Project(self.client, self.ghrep.project(id), self.organization)

    # def get_issues(self):
    #     for issue in self.ghrep.issues(state="Open"):
    #         yield issue

    # def get_issue(self, issue_id):
    #     return self.ghrep.issue(issue_id)

    # def get_autoassign_project(self):
    #     organizer_settings = self.get_organizer_settings()
    #     if not organizer_settings:
    #         return False
    #     if not "issues" in organizer_settings:
    #         return False
    #     if not "project_autoassign" in organizer_settings["issues"]:
    #         return False
    #     autoassign = organizer_settings["issues"]["project_autoassign"]
    #     if autoassign["organization"]:
    #         return self.organization.get_project_by_name(autoassign["name"])
    #     if autoassign["repository"]:
    #         return self.organization.get_repository(
    #             autoassign["repository"]
    #         ).get_project_by_name(autoassign["name"])
    #     return self.get_project_by_name(autoassign["name"])

    # def get_autoassign_column(self):
    #     organizer_settings = self.get_organizer_settings()
    #     project = self.get_autoassign_project()
    #     if not project:
    #         return False
    #     return project.get_column_by_name(
    #         organizer_settings["issues"]["project_autoassign"]["column"]
    #     )

    # def get_autoassign_labels(self):
    #     organizer_settings = self.get_organizer_settings()
    #     if (
    #         "issues" in organizer_settings
    #         and "auto_label" in organizer_settings["issues"]
    #     ):
    #         labels = set(organizer_settings["issues"]["auto_label"])
    #     else:
    #         labels = set([])
    #     if "labels" in self.organization.configuration:
    #         for label in self.organization.configuration["labels"]:
    #             if "repos" in label and self.name in label["repos"]:
    #                 labels.add(label["name"])
    #     if len(labels) > 0:
    #         return labels
    #     return False

    def create_branch(self, branch_name):
        """Create a branch in a repository"""
        current_default_branch = self.repository.get_branch(
            self.repository.default_branch
        )
        self.repository.create_branch_ref(
            branch_name, current_default_branch.latest_sha()
        )

    def branch_protection(
        self,
        branch: Branch,
        required_status_checks=None,
        enforce_admins: bool = True,
        require_review: bool = True,
        restrictions=None,
        required_linear_history: bool = NotSet,
        allow_force_pushes: bool = NotSet,
        required_approving_review_count: int = NotSet,
        require_code_owner_reviews: bool = NotSet,
        dismiss_stale_reviews: bool = NotSet,
        dismissal_restrictions=NotSet,
        bypass_restrictions=NotSet,
        lock_branch: bool = NotSet,
        allow_fork_syncing: bool = NotSet,
        block_creations: bool = NotSet,
        required_conversation_resolution: bool = NotSet,
        # allow_deletions: bool = False,
    ):
        """Update Branch Protection settings for a repository"""
        # required_status_checks
        # - strict - boolean
        # - contexts - array, leave empty for "all"
        if required_status_checks:
            if "contexts" not in required_status_checks:
                required_status_checks["contexts"] = []
            if "strict" not in required_status_checks:
                required_status_checks["strict"] = False

        # enforce_admins - boolean
        enforce_admins = bool(enforce_admins)

        # required_pull_request_reviews
        # - dismissal_restrictions - object (optional)
        #   - users - array
        #   - teams - array
        #   - apps - array
        # - dismiss_stale_reviews - boolean
        # - require_code_owner_reviews - boolean
        # - required_approving_review_count - integer
        if not require_review and not required_status_checks.get(
            "require_review", False
        ):
            try:
                branch.remove_protection()
            except GithubException as exception:
                print(
                    f"Error updating branch protections for {branch.name}: {exception}"
                )
            return

        # dismissal_restrictions
        # - users - array
        # - teams - array
        # - apps - array
        if dismissal_restrictions:
            for field in ["users", "teams", "apps"]:
                if field not in dismissal_restrictions:
                    dismissal_restrictions[field] = []
        # bypass_restrictions
        # - users - array
        # - teams - array
        # - apps - array
        if bypass_restrictions:
            for field in ["users", "teams", "apps"]:
                if field not in bypass_restrictions:
                    bypass_restrictions[field] = []
        # restrictions
        # - users - array
        # - teams - array
        # - apps - array
        if restrictions:
            for field in ["users", "teams", "apps"]:
                if field not in restrictions:
                    restrictions[field] = []
        try:
            branch.edit_protection(
                strict=required_status_checks.get("strict", NotSet),
                contexts=required_status_checks.get("contexts", NotSet),
                enforce_admins=enforce_admins,
                user_push_restrictions=restrictions.get("users", NotSet),
                team_push_restrictions=restrictions.get("teams", NotSet),
                app_push_restrictions=restrictions.get("apps", NotSet),
                dismissal_users=dismissal_restrictions.get("users", NotSet),
                dismissal_teams=dismissal_restrictions.get("teams", NotSet),
                dismissal_apps=dismissal_restrictions.get("apps", NotSet),
                users_bypass_pull_request_allowances=bypass_restrictions.get(
                    "users", NotSet
                ),
                teams_bypass_pull_request_allowances=bypass_restrictions.get(
                    "teams", NotSet
                ),
                apps_bypass_pull_request_allowances=bypass_restrictions.get(
                    "apps", NotSet
                ),
                dismiss_stale_reviews=dismiss_stale_reviews,
                require_code_owner_reviews=require_code_owner_reviews,
                required_approving_review_count=required_approving_review_count,
                required_linear_history=required_linear_history,
                allow_force_pushes=allow_force_pushes,
                lock_branch=lock_branch,
                allow_fork_syncing=allow_fork_syncing,
                block_creations=block_creations,
                required_conversation_resolution=required_conversation_resolution
                # allow_deletions = allow_deletions
            )
        except GithubException as exception:
            print(
                f"Error updating branch protections for {branch.name}: {exception.message}"
            )


# class OrganizerProject:
#     def __repr__(self):
#         return "OrganizerProject %s" % self.id

#     def __str__(self):
#         return self.__repr__()

#     def __init__(self, client, project, organization):
#         self.client = client
#         self.ghproject = project
#         self.organization = organization
#         self.id = project.id
#         self.name = project.name

#     def get_column(self, id):
#         return self.ghproject.column(id)

#     def get_columns(self):
#         for column in self.ghproject.columns():
#             yield column

#     def get_column_by_name(self, name):
#         def get_column_id_from_name(project, name):
#             for column in project.get_columns():
#                 if column.name == name:
#                     return column.id
#             return False

#         id = get_column_id_from_name(self, name)
#         if not id:
#             return False
#         return self.get_column(id)


def label_matches(config_label, label):
    """Check if a label matches the config"""
    if label.color != config_label.get("color", DEFAULT_LABEL_COLOR):
        return False
    if label.description != config_label.get("description", None):
        return False
    return True


class OrganizerTeam:
    """Class representing a GitHub Team"""

    def __repr__(self):
        return "OrganizerTeam %s/%s" % (self.organization.name, self.name)

    def __str__(self):
        return self.__repr__()

    def __init__(self, org: OrganizerOrganization, team: Team):
        """Inigtialize Class"""
        self.organization = org
        self.team = team
        self.name = team.name
        self._settings = org.get_configuration()

    def get_members(self):
        members = []
        for member in self.team.get_members():
            members.append(member)
        return members

    def get_user(self, username) -> NamedUser:
        headers, data = self.team._requester.requestJsonAndCheck(
            "GET", f"/users/{username}"
        )
        return NamedUser.NamedUser(self.team._requester, headers, data, completed=True)

    def update_members(self):
        # all_current_members = []
        new = self._settings.get("teams").get(self.name).get("members", [])
        for member in self.team.get_members():
            if member.login not in new:
                # all_current_members.append(member.login)
                self.team.remove_membership(member)
        for member in new:
            # if member not in all_current_members:
            username = member
            role = "member"
            if isinstance(member, dict):
                username = list(member.keys())[0]
                role = member.get(username).get("role", "member")
            try:
                user = self.get_user(username)
                self.team.add_membership(
                    member=user,
                    role=role,
                )
            except Exception as exception:
                print(f"Could not add user {username}: {exception}")
