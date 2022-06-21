"""
Split course names from the academic plans into its subject and number to get
its prerequisites.

Exports:
    `parse_course_name`, which takes the raw name of a course from an academic
    plan and attempts to get a course subject and number out of it, or None if
    it can't.
"""

import re
from typing import Literal, Optional, Tuple

__all__ = ["parse_course_name", "clean_course_title"]


def parse_course_name(
    name: str,
) -> Optional[Tuple[str, str, Optional[Literal["L", "X"]]]]:
    """
    Attempts to parse course name strings such as "MATH 10A/20A" into the course
    subject, which Curricular Analytics calls the prefix, and number.

    Returns a tuple of the prefix, number, and either L/X if the course is
    actually two courses and needs to be split as a physics lab or language
    analysis section.

    This function is in its own file because parsing course names from academic
    plans is somewhat complicated.

    Splitting course names is also necessary to get the prerequisites for the
    course.
    """
    # Based on
    # https://github.com/SheepTester-forks/ExploratoryCurricularAnalytics/blob/a9e6d0d7afb74f217b3efb382ed39cdd86fe0559/course_names.py#L13-L37
    name = name.strip("^* ")
    if name.startswith("ADV. CHEM"):
        return None
    name = re.sub(r"DF-?\d - ", "", name)
    match = re.search(
        r"\b([A-Z]{2,4}) *(\d+[A-Z]{0,2})(?: *[&/] *\d?[A-Z]([LX]))?", name
    )
    if match:
        subject, number, has_lab = match.group(1, 2, 3)
        if subject in ["IE", "RR"]:
            return None
        return subject, number, has_lab if has_lab == "L" or has_lab == "X" else None
    return None


def clean_course_title(title: str) -> str:
    """
    Cleans up the course title by removing asterisks and (see note)s.
    """
    title = title.strip("^* ¹")
    match = re.match(r"(GE|DEI) */ *(GE|AWP|DEI)", title)
    if match:
        return "DEI" if match.group(1) == "DEI" or match.group(2) == "DEI" else "GE"
    title = re.sub(r" */ *(GE|AWP|DEI)$", "", title, flags=re.I)
    title = re.sub(
        r" *\(\*?(see note|DEI APPROVED|DEI)\*?\)$|^1 ", "", title, flags=re.I
    )
    title = re.sub(r" +", " ", title)
    return title
