"""
Outputs a CSV file in Curricular Analytics' curriculum and degree plan formats
from the parsed academic plans and course prerequisites.

Exports:
    `output`, a generator function that takes a major code and optionally a
    college code and yields lines of the CSV file. You can use a for loop on the
    return value to print, write to a file, or store the lines in a string
    variable.
"""

from typing import Generator, Iterable, List, NamedTuple, Optional, Tuple

from parse import (
    CourseCode,
    MajorPlans,
    PlannedCourse,
    Prerequisite,
    major_plans,
    major_codes,
    prereqs,
)
from parse_course_name import parse_course_name

__all__ = ['output']

CourseId = str
Term = str


class CourseEntry(NamedTuple):
    code: Optional[CourseCode]
    course_name: str
    units: float
    id: int
    term: str
    major_course: bool

    def with_id(self, new_id: int) -> "CourseEntry":
        return CourseEntry(
            self.code,
            self.course_name,
            self.units,
            new_id,
            self.term,
            self.major_course,
        )


INSTITUTION = "University of California, San Diego"
SYSTEM_TYPE = "Quarter"
HEADER = [
    "Course ID",
    "Course Name",
    "Prefix",
    "Number",
    "Prerequisites",
    "Corequisites",
    "Strict-Corequisites",
    "Credit Hours",
    "Institution",
    "Canonical Name",
    "Term",
]
CURRICULUM_COLS = 10
DEGREE_PLAN_COLS = 11


def output_header(
    curriculum: str = "",
    degree_plan: Optional[str] = None,
    institution: str = "",
    degree_type: str = "",
    system_type: str = "",
    cip: str = "",
) -> Generator[List[str], None, None]:
    """
    Outputs the header for the CSV file. See Curricular Analytics'
    documentation for the CSV header format:
    https://curricularanalytics.org/files.
    """
    yield ["Curriculum", curriculum]
    if degree_plan is not None:
        yield ["Degree Plan", degree_plan]
    yield ["Institution", institution]
    yield ["Degree Type", degree_type]
    yield ["System Type", system_type]
    yield ["CIP", cip]


college_names = {
    "RE": "Revelle",
    "MU": "Muir",
    "TH": "Marshall",
    "WA": "Warren",
    "FI": "ERC",
    "SI": "Sixth",
    "SN": "Seventh",
}


def output_plan(
    major: MajorPlans, college: Optional[str] = None
) -> Generator[List[str], None, None]:
    """
    Outputs a curriculum or degree plan in Curricular Analytics' format (CSV).

    To output a degree plan, specify the college that the degree plan is for. If
    the college isn't specified, then `output_plan` will output the major's
    curriculum instead.
    """
    major_info = major_codes[major.major_code]
    # NOTE: Currently just gets the last listed award type (bias towards BS over
    # BA). Will see how to deal with BA vs BS
    yield from output_header(
        curriculum=major_info.name,
        degree_plan=college and f"{major_info.name}/ {college_names[college]}",
        institution=INSTITUTION,
        degree_type=list(major_info.award_types)[-1],
        system_type=SYSTEM_TYPE,
        cip=major_info.cip_code,
    )

    if college:

        def yield_courses() -> Generator[Tuple[PlannedCourse, bool, str], None, None]:
            for i, quarter in enumerate(major.plans[college].quarters, start=1):
                for course in quarter:
                    yield course, course.type == "DEPARTMENT" or course.overlaps_ge, str(
                        i
                    )

    else:

        def yield_courses() -> Generator[Tuple[PlannedCourse, bool, str], None, None]:
            for course in major.curriculum():
                yield course, True, ""

    courses: List[CourseEntry] = []
    major_id: int = 0
    college_id: int = 0

    def get_id(major_course: bool) -> int:
        """
        Helper function to get the next ID for a course. Not pure. Increments
        `major_id` or `college_id`, depending on whether `major_course` (whether
        the course is a major requirement) is true or not, and returns the new
        value.
        """
        nonlocal major_id, college_id
        if major_course:
            major_id += 1
            return major_id
        else:
            college_id += 1
            return college_id

    for course, major_course, term in yield_courses():
        course_name = course.course_code
        units = course.units
        if course_name == "MATH 11":
            # Override academic plan's math 11 units to 5.0 units per course
            # catalog. Must exactly match `MATH 11` because `MATH 11 OR PSYC 60`
            # probably should still be 4.0 units (#20)
            units = 5
        parsed = parse_course_name(course_name)
        code: Optional[Tuple[str, str]] = None
        if parsed:
            subject, number, has_lab = parsed
            code = subject, number
            if has_lab:
                units = 2 if has_lab == "L" else 2.5
                courses.append(
                    CourseEntry(
                        code,
                        f"{subject} {number}",
                        3 if has_lab == "L" else 2.5,
                        get_id(major_course),
                        term,
                        major_course,
                    )
                )
                course_name = f"{subject} {number}{has_lab}"
                code = subject, number + has_lab
        courses.append(
            CourseEntry(
                code, course_name, units, get_id(major_course), term, major_course
            )
        )

    # Count major courses (https://stackoverflow.com/a/157121)
    major_courses = sum(1 for course in courses if course.major_course)
    courses = [
        course if course.major_course else course.with_id(course.id + major_courses)
        for course in courses
    ]

    def find_prereq(
        prereq_ids: List[str], coreq_ids: List[str], alternatives: List[Prerequisite]
    ) -> None:
        for course in courses:
            for code, concurrent in alternatives:
                if course.code == code:
                    (coreq_ids if concurrent else prereq_ids).append(str(course.id))
                    return

    for major_course_section in True, False:
        if not college and not major_course_section:
            break
        yield ["Courses" if major_course_section else "Additional Courses"]
        yield HEADER
        for code, course_name, units, course_id, term, major_course in courses:
            if major_course != major_course_section:
                continue
            prefix, number = code or ("", "")
            prereq_ids: List[str] = []
            coreq_ids: List[str] = []
            if code in prereqs:
                for alternatives in prereqs[code]:
                    find_prereq(prereq_ids, coreq_ids, alternatives)

            yield [
                str(course_id),
                course_name.strip("*^ "),  # Asterisks seem to break the site
                prefix,
                number,
                ";".join(prereq_ids),
                ";".join(coreq_ids),
                "",
                f"{units:g}",  # https://stackoverflow.com/a/2440708
                "",
                "",
                term,
            ]


def rows_to_csv(rows: Iterable[List[str]], columns: int) -> Generator[str, None, None]:
    """
    Converts a list of lists of fields into lines of CSV records. Yields a
    newline-terminated line.

    The return value from `output_plan` should be passed as the `rows` argument.

    `output_plan` always outputs a "Term" column because I'm lazy, so this
    function can cut off extra columns or adds empty fields as needed to meet
    the column count.
    """
    for row in rows:
        yield (
            ",".join(
                [
                    f'"{field}"' if any(c in field for c in ",\r\n") else field
                    for field in row
                ][:columns]
                + [""] * (columns - len(row))
            )
            + "\n"
        )


def output(major: str, college: Optional[str] = None) -> Generator[str, None, None]:
    return rows_to_csv(
        output_plan(major_plans[major], college),
        DEGREE_PLAN_COLS if college else CURRICULUM_COLS,
    )


def to_file(path: str, csv: Iterable[str]) -> None:
    """
    Writes the records of the given CSV file to a file at the given path.

    For example, the following saves the CS major curriculum to
    `files/Curriculum-CS26.csv` and the ERC degree plan for CS to `files/Degree
    Plan-ERC-CS26.csv`.

    ```py
    to_file("files/Curriculum-CS26.csv", output("CS26"))
    to_file("files/Degree Plan-ERC-CS26.csv", output("CS26", 'FI'))
    ```
    """
    with open(path, "w") as file:
        file.writelines(csv)


if __name__ == "__main__":
    to_file("files/TH27_Revelle.csv", output("TH27", "RE"))
    for line in output("TH27"):
        print(line, end="")
