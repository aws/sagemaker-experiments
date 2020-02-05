"""
Invoke development tasks.
"""
from subprocess import check_output
from version import next_version_from_current_version
from subject_parser import SubjectParser
from release_manager import ReleaseManager


def recent_changes_to_src(last_version):
    stdout = check_output(["git", "log", "{}..HEAD".format(last_version), "--name-only", "--pretty=format: master"])
    stdout = stdout.decode("utf-8")
    lines = stdout.splitlines()
    src_lines = list(filter(lambda l: l.startswith("src"), lines))
    print(f"{len(src_lines)} src files changed since {last_version}")
    return src_lines


def get_changes(last_version):
    stdout = check_output(["git", "log", "{}..HEAD".format(last_version), "--pretty=format:%s"])
    stdout = stdout.decode("utf-8")
    changes = list(map(lambda line: line.strip(), stdout.splitlines()))
    print(f"{len(changes)} changes since last release {last_version}")
    return changes


def get_next_version(last_version, increment_type):
    # remove the 'v' prefix
    last_version = last_version[1:]
    return next_version_from_current_version(last_version, increment_type)


def get_version_increment_type(last_version):
    stdout = check_output(["git", "log", "{}..HEAD".format(last_version), "--pretty=format:%s"])
    stdout = stdout.decode("utf-8")
    subjects = stdout.splitlines()
    parsed_subjects = SubjectParser(subjects)
    return parsed_subjects.increment_type()


def release():
    """Creates a github release."""

    # get the last release tag
    stdout = check_output(["git", "describe", "--abbrev=0", "--tags"])
    stdout = stdout.decode("utf-8")
    last_version = stdout.strip()

    if not recent_changes_to_src(last_version):
        print("Nothing to release.")
        exit(1)
        return

    changes = get_changes(last_version)

    increment_type = get_version_increment_type(last_version)

    next_version = get_next_version(last_version, increment_type)

    manager = ReleaseManager(str(next_version), changes)
    manager.create_release()


def main():
    release()


if __name__ == "__main__":
    main()
