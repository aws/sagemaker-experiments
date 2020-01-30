import logging
import re


logger = logging.getLogger(__name__)


class SubjectParser:
    """
    Parses git commit subject lines to determine the type of change (breaking, feature, fix, etc...)
    """

    # order must be aligned with associated increment_type (major...post)
    _CHANGE_TYPES = ["breaking", "deprecation", "feature", "fix", "documentation", "infrastructure"]

    _PARSE_SUBJECT_REGEX = re.compile(
        r"""
        (?:(?P<label>break(?:ing)?|feat(?:ure)?|depr(?:ecation)?|change|fix|doc(?:umentation)?)\s*:)?
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    _CANONICAL_LABELS = {
        "break": "breaking",
        "feat": "feature",
        "depr": "deprecation",
        "change": "fix",
        "doc": "documentation",
    }

    _CHANGE_TO_INCREMENT_TYPE_MAP = {
        "breaking": "major",
        "feature": "minor",
        "deprecation": "minor",
        "fix": "patch",
        "change": "patch",
        "documentation": "patch",
    }

    _DEFAULT_LABEL = "fix"

    def __init__(self, subjects):
        self._groups = {}
        self._add_subjects(subjects)

    def _add_subjects(self, subjects):
        for subject in subjects:
            self._parse_subject(subject)

    def _parse_subject(self, subject):
        label = None
        match = SubjectParser._PARSE_SUBJECT_REGEX.search(subject)

        if match:
            label = match.group("label") or SubjectParser._DEFAULT_LABEL
            label = SubjectParser._CANONICAL_LABELS.get(label, label)
        else:
            print(f"no match {subject}")
            label = SubjectParser._DEFAULT_LABEL

        if label in self._groups:
            self._groups[label].append(subject)

    def increment_type(self):
        for change_type in SubjectParser._CHANGE_TYPES:
            if change_type in self._groups:
                return SubjectParser._CHANGE_TO_INCREMENT_TYPE_MAP[change_type]

        return "patch"
