from github import Github
import os
from pathlib import Path


class ReleaseManager:
    def __init__(self, version, changes):
        self._version = version
        self._changes = changes
        self._token = os.getenv("GITHUB_TOKEN")
        self._repo = os.getenv("GITHUB_REPOSITORY")
        if not self._token or not self._repo:
            raise ValueError("Missing required environment variables.")

    def create_release(self):
        tag = "v" + self._version
        name = f"Sagemaker Experiment SDK {tag}"
        template_text = Path(__file__).parent.joinpath("release_template.rst").read_text(encoding="UTF-8")
        change_list_content = "\n".join(list(map(lambda c: f"- {c}", self._changes)))
        message = template_text.format(version=tag, changes=change_list_content)
        g = Github(self._token)
        repo = g.get_repo(self._repo)
        repo.create_git_release(tag=tag, name=name, message=message, draft=False, prerelease=False)
        print(f"Created release {name}")
        print(f"See it at https://github.com/{self._repo}/releases")
