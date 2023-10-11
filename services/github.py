import os

from github import Auth, Github

# using an access token
auth = Auth.Token(os.getenv("ORG_TOKEN"))
# First create a Github instance:
# Public Web Github
gh = Github(auth=auth)
