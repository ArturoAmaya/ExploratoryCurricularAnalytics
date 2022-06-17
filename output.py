"""
Outputs a CSV file in Curricular Analytics' curriculum and degree plan formats
from the parsed academic plans and course prerequisites.

Exports:
    `output`, a generator function that takes a major code and optionally a
    college code and yields lines of the CSV file. You can use a for loop on the
    return value to print, write to a file, or store the lines in a string
    variable.
"""

from typing import Dict, Generator, Iterable, List, NamedTuple, Optional
from college_names import college_names

from parse import (
    CourseCode,
    MajorPlans,
    PlannedCourse,
    Prerequisite,
    major_plans,
    major_codes,
    prereqs,
)
from parse_course_name import clean_course_title, parse_course_name

__all__ = ["MajorOutput"]

CourseId = str
Term = str


class ProcessedCourse(NamedTuple):
    course_title: str
    code: CourseCode
    units: float
    major_course: bool
    term: int


class InputCourse(NamedTuple):
    course: PlannedCourse
    major_course: bool
    term: int

    def process(
        self,
        code: Optional[CourseCode] = None,
        course_title: Optional[str] = None,
        units: Optional[float] = None,
    ) -> ProcessedCourse:
        if course_title is None:
            course_title = self.course.course_title
        if units is None:
            units = self.course.units
        return ProcessedCourse(
            course_title, code or ("", ""), units, self.major_course, self.term
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


class MajorOutput:
    """
    Keeps track of the course IDs used by a curriculum.
    """

    plans: MajorPlans
    course_ids: Dict[CourseCode, int]
    curriculum: List[PlannedCourse]
    start_id = 1

    def __init__(self, major_code: str) -> None:
        self.plans = major_plans[major_code]
        self.course_ids = {}
        self.curriculum = self.plans.curriculum()
        self.populate_course_ids()

    def populate_course_ids(self) -> None:
        for course in self.curriculum:
            parsed = parse_course_name(course.course_title)
            if parsed:
                subject, number, has_lab = parsed
                code = subject, number
                if code not in self.course_ids:
                    self.course_ids[code] = self.start_id
                    self.start_id += 1
                if has_lab:
                    code = subject, number + has_lab
                    if code not in self.course_ids:
                        self.course_ids[code] = self.start_id
                        self.start_id += 1

    def output_plan(
        self, college: Optional[str] = None
    ) -> Generator[List[str], None, None]:
        """
        Outputs a curriculum or degree plan in Curricular Analytics' format (CSV).

        To output a degree plan, specify the college that the degree plan is for. If
        the college isn't specified, then `output_plan` will output the major's
        curriculum instead.
        """
        major_info = major_codes[self.plans.major_code]
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

        # 1. Get the courses
        course_input: Generator[InputCourse, None, None] = (
            (
                InputCourse(
                    course, course.type == "DEPARTMENT" or course.overlaps_ge, i
                )
                for i, quarter in enumerate(self.plans.plans[college].quarters, start=1)
                for course in quarter
            )
            if college
            else (InputCourse(course, True, 0) for course in self.curriculum)
        )

        # 2. Split lab courses
        processed_courses: List[ProcessedCourse] = []
        for input_course in course_input:
            if input_course.course.course_title == "MATH 11":
                # Override academic plan's math 11 units to 5.0 units per course
                # catalog. Must exactly match `MATH 11` because `MATH 11 OR PSYC 60`
                # probably should still be 4.0 units (#20)
                processed_courses.append(input_course.process(("MATH", "11"), units=5))
                continue

            parsed = parse_course_name(input_course.course.course_title)
            if parsed:
                subject, number, has_lab = parsed
                code = subject, number
                if has_lab:
                    processed_courses.append(
                        input_course.process(
                            code, f"{subject} {number}", 3 if has_lab == "L" else 2.5
                        )
                    )
                    processed_courses.append(
                        input_course.process(
                            (subject, number + has_lab),
                            f"{subject} {number}{has_lab}",
                            2 if has_lab == "L" else 2.5,
                        )
                    )
                else:
                    processed_courses.append(input_course.process(code))
            else:
                processed_courses.append(input_course.process())

        # 3. Assign course IDs
        current_id = self.start_id
        course_ids = {**self.course_ids}
        for course in processed_courses:
            if course.code and course.code not in course_ids:
                course_ids[course.code] = current_id
                current_id += 1

        def find_prereq(
            prereq_ids: List[int],
            coreq_ids: List[int],
            alternatives: List[Prerequisite],
        ) -> None:
            for course in processed_courses:
                if course.code is None:
                    continue
                for code, concurrent in alternatives:
                    if course.code == code:
                        (coreq_ids if concurrent else prereq_ids).append(
                            course_ids[course.code]
                        )
                        return

        # 4. Get prerequisites and output
        # In case there are duplicate courses, only let a course in course_ids
        # get used once
        claimed_ids = set(course_ids.keys())
        for major_course_section in True, False:
            if not college and not major_course_section:
                break
            yield ["Courses" if major_course_section else "Additional Courses"]
            yield HEADER
            for course_title, code, units, major_course, term in processed_courses:
                if major_course != major_course_section:
                    continue

                if code in claimed_ids:
                    course_id = course_ids[code]
                    claimed_ids.remove(code)
                else:
                    course_id = current_id
                    current_id += 1

                prereq_ids: List[int] = []
                coreq_ids: List[int] = []
                # Math 18 has no prereqs because it only requires pre-calc,
                # which we assume the student has credit for
                if code in prereqs and code != ("MATH", "18"):
                    for alternatives in prereqs[code]:
                        find_prereq(prereq_ids, coreq_ids, alternatives)

                subject, number = code
                yield [
                    str(course_id),
                    clean_course_title(course_title),
                    subject,
                    number,
                    ";".join(map(str, prereq_ids)),
                    ";".join(map(str, coreq_ids)),
                    "",
                    f"{units:g}",  # https://stackoverflow.com/a/2440708
                    "",
                    "",
                    str(term),
                ]

    def output(self, college: Optional[str] = None) -> str:
        cols = DEGREE_PLAN_COLS if college else CURRICULUM_COLS
        csv = ""
        for line in rows_to_csv(self.output_plan(college), cols):
            csv += line
        return csv


if __name__ == "__main__":
    import sys

    print(MajorOutput(sys.argv[1]).output(sys.argv[2] if len(sys.argv) > 2 else None))
