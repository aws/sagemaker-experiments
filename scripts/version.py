import re


# a subset of PEP 440
_VERSION_REGEX = re.compile(
    r"""
    ^\s*
    v?
    (?P<major>\d+)
    (?:\.(?P<minor>\d+))?
    (?:\.(?P<patch>\d+))?
    \s*$
""",
    re.VERBOSE | re.IGNORECASE,
)


class Version:
    """
    Represents a major.minor.patch version string
    """

    def __init__(self, major, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

        self.tag = f"v{str(self)}"

    def __str__(self):
        parts = [str(x) for x in [self.major, self.minor, self.patch]]

        return ".".join(parts).lower()

    def increment(self, increment_type):
        incr = None
        if increment_type == "major":
            incr = Version(self.major + 1)
        elif increment_type == "minor":
            incr = Version(self.major, self.minor + 1)
        elif increment_type == "patch":
            incr = Version(self.major, self.minor, self.patch + 1)

        return incr


def parse(version):
    match = _VERSION_REGEX.search(version)
    if not match:
        raise ValueError(f"invalid version: {version}")

    return Version(int(match.group("major") or 0), int(match.group("minor") or 0), int(match.group("patch") or 0),)


def next_version_from_current_version(current_version, increment_type):
    return parse(current_version).increment(increment_type)
