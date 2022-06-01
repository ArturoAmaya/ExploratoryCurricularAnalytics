"""
handles output in happy csv format
"""

from typing import Generator, Iterable, List, Optional

from parse import Major, majors, major_codes


INSTITUTION = "University of California, San Diego"
SYSTEM_TYPE = "Quarter"


def rows_to_csv(rows: Iterable[List[str]], columns: int) -> Generator[str, None, None]:
    for row in rows:
        yield (
            ",".join(
                [f'"{field}"' if "," in field else field for field in row]
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
    yield ["Courses"]


# TODO: Curriculum and degree plan are similar enough to be merged, reduce
# repetition I think


def output_curriculum(major: Major) -> Generator[List[str], None, None]:
    """
    Outputs a curriculum in Curricular Analytics' format (CSV).
    """
    major_info = major_codes[major.major]
    # NOTE: Currently just gets the last listed award type (bias towards BS over
    # BA). Will see how to deal with BA vs BS
    yield from output_header(
        curriculum=major_info.name,
        institution=INSTITUTION,
        degree_type=list(major_info.award_types)[-1],
        system_type=SYSTEM_TYPE,
        cip=major_info.cip_code,
    )
    yield [
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
    ]
    for i, course in enumerate(major.curriculum()):
        yield [
            str(i + 1),
            course.course,
            "TODO: subject",
            "TODO: number",
            "TODO: prereqs",
            "TODO: coreqs",
            "",
            str(course.units),
            "",
            "",
        ]


college_names = {
    "RE": "Revelle",
    "MU": "Muir",
    "TH": "Marshall",
    "WA": "Warren",
    "FI": "ERC",
    "SI": "Sixth",
    "SN": "Seventh",
}


def output_degree_plan(major: Major, college: str) -> Generator[List[str], None, None]:
    """
    Outputs the given college's degree plan in Curricular Analytics' format
    (CSV).
    """
    major_info = major_codes[major.major]
    # NOTE: Currently just gets the last listed award type (bias towards BS over
    # BA). Will see how to deal with BA vs BS
    yield from output_header(
        curriculum=major_info.name,
        degree_plan=f"{major_info}/ {college_names[college]}",
        institution=INSTITUTION,
        degree_type=list(major_info.award_types)[-1],
        system_type=SYSTEM_TYPE,
        cip=major_info.cip_code,
    )
    yield [
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
    id = 1
    for i, quarter in enumerate(major.plans[college].quarters):
        for course in quarter:
            if course.type == "DEPARTMENT" or course.overlaps_ge:
                yield [
                    str(id + 1),
                    course.course,
                    "TODO: subject",
                    "TODO: number",
                    "TODO: prereqs",
                    "TODO: coreqs",
                    "",
                    str(course.units),
                    "",
                    "",
                    str(i + 1),
                ]
            id += 1
    yield ["Additional Courses"]
    yield [
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
    for i, quarter in enumerate(major.plans[college].quarters):
        for course in quarter:
            if not (course.type == "DEPARTMENT" or course.overlaps_ge):
                yield [
                    str(id + 1),
                    course.course,
                    "TODO: subject",
                    "TODO: number",
                    "TODO: prereqs",
                    "TODO: coreqs",
                    "",
                    str(course.units),
                    "",
                    "",
                    str(i + 1),
                ]
            id += 1


if __name__ == "__main__":
    for line in rows_to_csv(output_curriculum(majors["CS26"]), 10):
        print(line, end="")
