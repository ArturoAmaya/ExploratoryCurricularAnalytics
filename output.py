"""
handles output in happy csv format
"""

from typing import Dict, Generator, Iterable, List, Optional, Tuple

from parse import Course, Major, PlannedCourse, majors, major_codes, prereqs
from parse_course_name import parse_course_name

Term = str
CourseOrder = Tuple[Course, PlannedCourse, Term]


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
    Outputs a curriculum in Curricular Analytics' format (CSV).
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

    course_ids: Dict[Tuple[str, str], str] = {}
    main_courses: List[CourseOrder] = []
    additional_courses: List[CourseOrder] = []
    if college:
        for i, quarter in enumerate(major.plans[college].quarters):
            for course in quarter:
                prefix_number = parse_course_name(course.course)
                (
                    main_courses
                    if course.type == "DEPARTMENT" or course.overlaps_ge
                    else additional_courses
                ).append((prefix_number, course, str(i + 1)))
        id = 1
        for prefix_number, _, _ in main_courses:
            course_ids[prefix_number] = str(id)
            id += 1
        for prefix_number, _, _ in additional_courses:
            course_ids[prefix_number] = str(id)
            id += 1
    else:
        for i, course in enumerate(major.curriculum()):
            prefix_number = parse_course_name(course.course)
            course_ids[prefix_number] = str(i + 1)
            main_courses.append((prefix_number, course, ""))

    for courses in main_courses, additional_courses:
        if not college and courses is additional_courses:
            break
        yield ["Courses" if courses is main_courses else "Additional Courses"]
        yield HEADER
        for (prefix, number), course, term in courses:
            prereq_ids: List[str] = []
            coreq_ids: List[str] = []
            if (prefix, number) in prereqs:
                for alternatives in prereqs[prefix, number]:
                    for course_code, concurrent in alternatives:
                        if course_code in course_ids:
                            (coreq_ids if concurrent else prereq_ids).append(
                                course_ids[course_code]
                            )
            yield [
                course_ids[prefix, number],
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


if __name__ == "__main__":
    for line in rows_to_csv(output_plan(majors["CS26"], "SI"), DEGREE_PLAN_COLS):
        print(line, end="")
