"""
Outputs a CSV file in Curricular Analytics' curriculum and degree plan formats
from the parsed academic plans and course prerequisites.
"""

from typing import Dict, Generator, Iterable, List, NamedTuple, Optional

from parse import (
    Course as CourseCode,
    Major,
    PlannedCourse,
    majors,
    major_codes,
    prereqs,
)
from parse_course_name import parse_course_name

CourseId = str
Term = str


class CourseEntry(NamedTuple):
    code: CourseCode
    course: PlannedCourse
    id: str
    term: str

    def with_id(self, new_id: str) -> "CourseEntry":
        return CourseEntry(self.code, self.course, new_id, self.term)


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


def rows_to_csv(rows: Iterable[List[str]], columns: int) -> Generator[str, None, None]:
    """
    Converts a list of lists of fields into lines of CSV records. Yields a
    newline-terminated line.

    `output_plan` always outputs a "Term" column because I'm lazy, so this
    function cuts off extra columns for curricula.

    For example, the following saves the output CSV of the bioengineering
    curriculum to a string variable.

    ```py
    csv = ""
    for line in rows_to_csv(output_plan(majors["BE25"]), CURRICULUM_COLS):
        csv += line
    ```
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
    major: Major, college: Optional[str] = None
) -> Generator[List[str], None, None]:
    """
    Outputs a curriculum or degree plan in Curricular Analytics' format (CSV).

    To output a degree plan, specify the college that the degree plan is for. If
    the college isn't specified, then `output_plan` will output the major's
    curriculum instead.
    """
    major_info = major_codes[major.major]
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

    course_ids: Dict[CourseCode, str] = {}
    main_courses: List[CourseEntry] = []
    additional_courses: List[CourseEntry] = []
    if college:
        for i, quarter in enumerate(major.plans[college].quarters):
            for course in quarter:
                code = parse_course_name(course.course)
                (
                    main_courses
                    if course.type == "DEPARTMENT" or course.overlaps_ge
                    else additional_courses
                ).append(CourseEntry(code, course, "", str(i + 1)))
        main_courses = [
            entry.with_id(str(i + 1)) for i, entry in enumerate(main_courses)
        ]
        additional_courses = [
            entry.with_id(str(len(main_courses) + i + 1))
            for i, entry in enumerate(additional_courses)
        ]
        for entry in main_courses:
            course_ids[entry.code] = entry.id
        for entry in additional_courses:
            course_ids[entry.code] = entry.id
    else:
        for i, course in enumerate(major.curriculum()):
            code = parse_course_name(course.course)
            course_ids[code] = str(i + 1)
            main_courses.append(CourseEntry(code, course, str(i + 1), ""))

    for courses in main_courses, additional_courses:
        if not college and courses is additional_courses:
            break
        yield ["Courses" if courses is main_courses else "Additional Courses"]
        yield HEADER
        for (prefix, number), course, course_id, term in courses:
            prereq_ids: List[str] = []
            coreq_ids: List[str] = []
            if (prefix, number) in prereqs:
                for alternatives in prereqs[prefix, number]:
                    for code, concurrent in alternatives:
                        if code in course_ids:
                            (coreq_ids if concurrent else prereq_ids).append(
                                course_ids[code]
                            )
            yield [
                course_id,
                course.course,
                prefix,
                number,
                ";".join(prereq_ids),
                ";".join(coreq_ids),
                "",
                f"{course.units:g}",  # https://stackoverflow.com/a/2440708
                "",
                "",
                term,
            ]


def to_file(path: str, csv: Iterable[str]) -> None:
    """
    Writes the records of the given CSV file to a file at the given path.

    For example, the following saves the CS major curriculum to
    `files/Curriculum-CS26.csv`.

    ```py
    to_file(
        "files/Curriculum-CS26.csv",
        rows_to_csv(output_plan(majors["CS26"]), DEGREE_PLAN_COLS),
    )
    ```
    """
    with open(path, "w") as file:
        file.writelines(csv)


if __name__ == "__main__":
    for line in rows_to_csv(output_plan(majors["CS26"], "SI"), DEGREE_PLAN_COLS):
        print(line, end="")
