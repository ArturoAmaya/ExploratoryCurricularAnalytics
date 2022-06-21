"""
Outputs a CSV file in Curricular Analytics' curriculum and degree plan formats
from the parsed academic plans and course prerequisites.

Exports:
    `output`, a generator function that takes a major code and optionally a
    college code and yields lines of the CSV file. You can use a for loop on the
    return value to print, write to a file, or store the lines in a string
    variable.
"""

from typing import Dict, Generator, Iterable, List, NamedTuple, Optional, Set, Union
from college_names import college_names
from output_json import Curriculum, Item, Term, Requisite

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

non_course_prereqs: Dict[str, List[CourseCode]] = {
    "SOCI- UD METHODOLOGY": [("SOCI", "60")],
    "TDHD XXX": [("TDTR", "10")],
}


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
            clean_course_title(course_title),
            code or ("", ""),
            units,
            self.major_course,
            self.term,
        )


class OutputCourse(NamedTuple):
    course_id: int
    course_title: str
    code: CourseCode
    prereq_ids: List[int]
    coreq_ids: List[int]
    units: float
    term: int


class OutputCourses:
    processed_courses: List[ProcessedCourse]
    current_id: int
    course_ids: Dict[CourseCode, int]
    duplicate_titles: Dict[str, int]
    claimed_ids: Set[CourseCode]
    degree_plan: bool

    def __init__(
        self,
        processed_courses: List[ProcessedCourse],
        start_id: int,
        course_ids: Dict[CourseCode, int],
        degree_plan: bool,
    ) -> None:
        self.processed_courses = processed_courses
        self.degree_plan = degree_plan

        # 3. Assign course IDs
        self.current_id = start_id
        self.course_ids = course_ids
        for course in processed_courses:
            if course.code and course.code not in course_ids:
                course_ids[course.code] = self.current_id
                self.current_id += 1

        # Get duplicate course titles so can start with "GE 1" and so on
        course_titles = [course.course_title for course in processed_courses]
        self.duplicate_titles = {
            title: 0
            for i, title in enumerate(course_titles)
            if title in course_titles[0:i]
        }

        # In case there are duplicate courses, only let a course in course_ids
        # get used once
        self.claimed_ids = set(course_ids.keys())

    # 4. Get prerequisites
    def find_prereq(
        self,
        prereq_ids: List[int],
        coreq_ids: List[int],
        alternatives: List[Prerequisite],
        before: Union[int, CourseCode],
    ) -> None:
        # Find first processed course whose code is in `alternatives`
        for course in self.processed_courses:
            if course.code is None:
                continue
            # Assumes processed courses are chronological
            if isinstance(before, int):
                if course.term >= before:
                    return
            else:
                if course.code == before:
                    return
            for code, concurrent in alternatives:
                if course.code == code:
                    (coreq_ids if concurrent else prereq_ids).append(
                        self.course_ids[course.code]
                    )
                    return

    def list_courses(
        self, show_major: Optional[bool] = None
    ) -> Generator[OutputCourse, None, None]:
        for course_title, code, units, major_course, term in self.processed_courses:
            if show_major is not None and major_course != show_major:
                continue

            if code in self.claimed_ids:
                course_id = self.course_ids[code]
                self.claimed_ids.remove(code)
            else:
                course_id = self.current_id
                self.current_id += 1

            prereq_ids: List[int] = []
            coreq_ids: List[int] = []
            # Math 18 has no prereqs because it only requires pre-calc,
            # which we assume the student has credit for
            if course_title in non_course_prereqs:
                for prereq in non_course_prereqs[course_title]:
                    self.find_prereq(
                        prereq_ids, coreq_ids, [Prerequisite(prereq, False)]
                    )
            elif code in prereqs and code != ("MATH", "18"):
                for alternatives in prereqs[code]:
                    self.find_prereq(
                        prereq_ids,
                        coreq_ids,
                        alternatives,
                        term if self.degree_plan else code,
                    )

            if course_title in self.duplicate_titles:
                self.duplicate_titles[course_title] += 1
                course_title = f"{course_title} {self.duplicate_titles[course_title]}"

            yield OutputCourse(
                course_id, course_title, code, prereq_ids, coreq_ids, units, term
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

    def get_courses(self, college: Optional[str]) -> OutputCourses:
        # 1. Get the courses
        course_input: Generator[InputCourse, None, None] = (
            (
                InputCourse(
                    course, course.type == "DEPARTMENT" or course.overlaps_ge, i
                )
                for i, quarter in enumerate(self.plans.plans[college].quarters)
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

        return OutputCourses(
            processed_courses, self.start_id, {**self.course_ids}, bool(college)
        )

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

        processed = self.get_courses(college)

        for major_course_section in True, False:
            if not college and not major_course_section:
                break
            yield ["Courses" if major_course_section else "Additional Courses"]
            yield HEADER
            for (
                course_id,
                course_title,
                (subject, number),
                prereq_ids,
                coreq_ids,
                units,
                term,
            ) in processed.list_courses(major_course_section):
                yield [
                    str(course_id),
                    course_title,
                    subject,
                    number,
                    ";".join(map(str, prereq_ids)),
                    ";".join(map(str, coreq_ids)),
                    "",
                    f"{units:g}",  # https://stackoverflow.com/a/2440708
                    "",
                    "",
                    str(term + 1),
                ]

    def output_json(self, college: Optional[str] = None) -> Curriculum:
        curriculum = Curriculum(
            curriculum_terms=[
                Term(id=i + 1, curriculum_items=[]) for i in range(12 if college else 1)
            ]
        )
        for (
            course_id,
            course_title,
            _,
            prereq_ids,
            coreq_ids,
            units,
            term,
        ) in self.get_courses(college).list_courses():
            curriculum["curriculum_terms"][term]["curriculum_items"].append(
                Item(
                    name=course_title,
                    id=course_id,
                    credits=units,
                    curriculum_requisites=[
                        Requisite(
                            source_id=prereq_id, target_id=course_id, type="prereq"
                        )
                        for prereq_id in prereq_ids
                    ]
                    + [
                        Requisite(source_id=coreq_id, target_id=course_id, type="coreq")
                        for coreq_id in coreq_ids
                    ],
                )
            )
        return curriculum

    def output(self, college: Optional[str] = None) -> str:
        if college is not None and college not in self.plans.plans:
            raise KeyError(f"No degree plan available for {college}.")
        cols = DEGREE_PLAN_COLS if college else CURRICULUM_COLS
        csv = ""
        for line in rows_to_csv(self.output_plan(college), cols):
            csv += line
        return csv


if __name__ == "__main__":
    import sys

    print(MajorOutput(sys.argv[1]).output(sys.argv[2] if len(sys.argv) > 2 else None))
