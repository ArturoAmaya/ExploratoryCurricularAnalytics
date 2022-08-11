"""
Parses the prerequisite and academic plan CSV files into objects for easier
manipulation.

Exports:
    `prereqs`, a dictionary mapping from a subject code-number tuple to a list
    of prerequisites, which are each lists of possible course codes to satisfy
    the requirement.

    `major_plans`, a dictionary mapping from ISIS major codes to `MajorPlans`
    objects, which contains a dictionary mapping college codes to `Plan`s, which
    have a list of list of `PlannedCourse`s for each quarter.

    `major_codes`, a dictionary mapping from ISIS major codes to `MajorInfo`
    objects, which contains data from the ISIS major codes spreadsheet.
"""

from functools import total_ordering
from typing import Dict, List, Literal, NamedTuple, Optional, Set, Tuple

__all__ = ["prereqs", "major_plans", "major_codes"]

CourseCode = Tuple[str, str]


def read_csv_from(
    path: str, not_found_msg: Optional[str] = None, strip: bool = False
) -> List[List[str]]:
    """
    Reads and parses the file at the given path as a CSV file.

    The CSV parser doesn't validate the CSV, so it's kind of dumb, but I don't
    think much cleverness is needed for parsing these fairly tame CSV files.
    There is support for quoted fields and rudimentary support for backslashes
    (they won't break, but they're currently not interpreted, so `\\"` remains
    in the field value).

    This function returns a list of records (rows), each containing the fields
    of the record. Quoted fields have their double quotes removed.

    Since I gitignored the CSV files, I'm using `not_found_msg` to give more
    helpful error messages in case someone running this code hasn't put the
    necessary CSV files in files/ folder.

    Set `strip` to true to remove whitespace padding from record fields.
    """
    rows: List[List[str]] = []

    def parse_field(field: str) -> str:
        """
        Helper function to process a raw field from the CSV file. Removes quotes
        from quoted fields and strips whitespace if desired.
        """
        if len(field) > 0 and field[0] == '"':
            field = field[1:-1].replace('""', '"')
        return field.strip() if strip else field

    try:
        with open(path, "r") as file:
            row_overflow: Optional[Tuple[List[str], str]] = None
            for line in file.read().splitlines():
                row: List[str]
                in_quotes: bool
                if row_overflow:
                    row = row_overflow[0]
                    in_quotes = True
                else:
                    row = []
                    rows.append(row)
                    in_quotes = False
                last_index: int = 0
                for i, char in enumerate(line + ","):
                    if in_quotes:
                        if char == '"':
                            in_quotes = False
                    else:
                        if char == '"':
                            in_quotes = True
                        elif char == ",":
                            prefix: str = row_overflow[1] if row_overflow else ""
                            row_overflow = None
                            row.append(parse_field(prefix + line[last_index:i]))
                            last_index = i + 1
                if in_quotes:
                    prefix: str = row_overflow[1] if row_overflow else ""
                    row_overflow = row, prefix + line[last_index:] + "\n"
    except FileNotFoundError as e:
        raise e if not_found_msg is None else FileNotFoundError(not_found_msg)
    return rows


class Prerequisite(NamedTuple):
    course_code: CourseCode
    allow_concurrent: bool


@total_ordering
class TermCode(str):
    quarters = ["WI", "SP", "S1", "S2", "S3", "SU", "FA"]

    def quarter_value(self) -> int:
        return TermCode.quarters.index(self[0:2])

    def year(self) -> int:
        # Assumes 21st century (all the plans we have are in the 21st century)
        return 2000 + int(self[2:4])

    def __lt__(self, other: str) -> bool:
        if not isinstance(other, TermCode):
            raise NotImplemented
        if self.year() == other.year():
            return self.quarter_value() < other.quarter_value()
        else:
            return self.year() < other.year()


def prereq_rows_to_dict(
    rows: List[List[str]],
) -> Dict[TermCode, Dict[CourseCode, List[List[Prerequisite]]]]:
    """
    Converts prerequisite rows from a CSV to a nested dictionary mapping from a
    term code (e.g. FA12) to a course code to its prerequisites.

    The dictionary values are lists of lists. The outer list is a list of
    requirements, like an AND, while each inner list is a list of possible
    courses to satisfy the requirement, like an OR.
    """
    terms: Dict[TermCode, Dict[CourseCode, List[List[Prerequisite]]]] = {}
    for (
        term,  # Term Code
        _,  # Term ID
        _,  # Course ID
        subject,  # Course Subject Code
        number,  # Course Number
        req_id,  # Prereq Sequence ID
        _,  # Prereq Course ID
        req_subj,  # Prereq Subject Code
        req_num,  # Prereq Course Number
        _,  # Prereq Minimum Grade Priority
        _,  # Prereq Minimum Grade
        allow_concurrent,  # Allow concurrent registration
    ) in rows:
        term = TermCode(term)
        if term not in terms:
            terms[term] = {}
        course: CourseCode = subject, number
        prereq = Prerequisite((req_subj, req_num), allow_concurrent == "Y")
        if course not in terms[term]:
            terms[term][course] = []
        if req_id == "":
            continue
        index = int(req_id) - 1
        while len(terms[term][course]) <= index:
            terms[term][course].append([])
        # Could probably include the allow concurrent registration info here
        terms[term][course][index].append(prereq)
    return terms


_prereqs: Optional[Dict[TermCode, Dict[CourseCode, List[List[Prerequisite]]]]] = None


def prereqs(term: str) -> Dict[CourseCode, List[List[Prerequisite]]]:
    global _prereqs
    if _prereqs is None:
        _prereqs = prereq_rows_to_dict(
            read_csv_from(
                "./files/prereqs_fa12.csv",
                "There is no `prereqs_fa12.csv` file in the files/ folder. See the README for where to download it from.",
                strip=True,
            )[1:]
        )
        # Fix possible errors in prereqs (#52)
        for term_prereqs in _prereqs.values():
            term_prereqs["NANO", "102"] = [[Prerequisite(("CHEM", "6C"), False)]]
            term_prereqs["DOC", "2"] = [[Prerequisite(("DOC", "1"), False)]]
    term = TermCode(term)
    if term not in _prereqs:
        first_term = min(_prereqs.keys())
        if term < first_term:
            term = first_term
        else:
            term = max(_prereqs.keys())
    return _prereqs[term]


class PlannedCourse(NamedTuple):
    """
    Represents a course in an academic plan.
    """

    course_title: str
    units: float
    type: Literal["COLLEGE", "DEPARTMENT"]
    overlaps_ge: bool


class Plan(NamedTuple):
    """
    Represents a college-specific academic plan. Can be used to create degree
    plans for Curricular Analytics.

    `quarters` is always of length 16, with four sequences of
    fall-winter-spring-summer. Yes, some plans do, namely 2014 CLLA DP and 2020
    CG35 SN, which are already known to be oddballs. Plans shouldn't be
    including summer sessions, but some older plans do anyways.
    """

    quarters: List[List[PlannedCourse]]


class MajorPlans(NamedTuple):
    """
    Represents a major's set of academic plans. Contains plans for each college.

    To get the plan for a specific college, use the two-letter college code. For
    example, `plans["FI"]` contains the academic plan for ERC (Fifth College).
    """

    # College codes from least to most weird colleges (see #14)
    least_weird_colleges = ["TH", "WA", "SN", "MU", "FI", "RE", "SI"]

    year: int
    department: str
    major_code: str
    plans: Dict[str, Plan]

    def curriculum(self, college: Optional[str] = None) -> List[PlannedCourse]:
        """
        Returns a list of courses based on the specified college's degree plan
        with college-specific courses removed. Can be used to create a
        curriculum for Curricular Analytics.

        Two curricula are equivalent if they have the same of each number of
        course, regardless of the order. However, there can be multiple
        identical courses (eg "ELECTIVE"), so this method does not return a set.

        The `overlaps_ge` attribute for these courses should be ignored (because
        there is no college whose GEs the course overlaps with).

        If no college is specified, it will try Marshall (Third College) by
        default because it appears to be a generally good college to base
        curricula off of (see #14). If there is no Marshall plan, it will try a
        different college.
        """
        if college is None:
            for college_code in MajorPlans.least_weird_colleges:
                if college_code in self.plans:
                    college = college_code
                    break
            if college is None:
                raise KeyError("Major has no college plans.")
        return [
            course
            for quarter in self.plans[college].quarters
            for course in quarter
            if course.type == "DEPARTMENT" or course.overlaps_ge
        ]


def plan_rows_to_dict(rows: List[List[str]]) -> Dict[int, Dict[str, MajorPlans]]:
    """
    Converts the academic plans CSV rows into a dictionary of major codes to
    `Major` objects.
    """
    years: Dict[int, Dict[str, MajorPlans]] = {}
    for (
        department,  # Department
        major_code,  # Major
        college_code,  # College
        course_title,  # Course
        units,  # Units
        course_type,  # Course Type
        overlap,  # GE/Major Overlap
        year,  # Start Year
        plan_yr,  # Year Taken
        plan_qtr,  # Quarter Taken
        _,  # Term Taken
    ) in rows:
        year = int(year)
        if year not in years:
            years[year] = {}
        if major_code not in years[year]:
            years[year][major_code] = MajorPlans(year, department, major_code, {})
        if college_code not in years[year][major_code].plans:
            years[year][major_code].plans[college_code] = Plan([[] for _ in range(16)])
        quarter = (int(plan_yr) - 1) * 4 + int(plan_qtr) - 1
        if course_type != "COLLEGE" and course_type != "DEPARTMENT":
            raise TypeError('Course type is neither "COLLEGE" nor "DEPARTMENT"')
        years[year][major_code].plans[college_code].quarters[quarter].append(
            PlannedCourse(course_title, float(units), course_type, overlap == "Y")
        )
    return years


_major_plans: Optional[Dict[int, Dict[str, MajorPlans]]] = None


def major_plans(year: int) -> Dict[str, MajorPlans]:
    global _major_plans
    if _major_plans is None:
        _major_plans = plan_rows_to_dict(
            read_csv_from(
                "./files/academic_plans_fa12.csv",
                "There is no `academic_plans_fa12.csv` file in the files/ folder. See the README for where to download it from.",
                strip=True,
            )[1:]
        )
    return _major_plans[year]


class MajorInfo(NamedTuple):
    """
    Represents information about a major from the ISIS major code list.

    You can find the major code list by Googling "isis major codes," but it's
    not going to be in the format that this program expects:
    https://blink.ucsd.edu/_files/instructors-tab/major-codes/isis_major_code_list.xlsx
    """

    isis_code: str
    name: str
    department: str
    cip_code: str
    award_types: Set[str]


def major_rows_to_dict(rows: List[List[str]]) -> Dict[str, MajorInfo]:
    majors: Dict[str, MajorInfo] = {}
    for (
        _,  # Previous Local Code
        _,  # UCOP Major Code (CSS)
        isis_code,  # ISIS Major Code
        _,  # Major Abbreviation
        _,  # Major Description
        title,  # Diploma Title
        _,  # Start Term
        _,  # End Term
        _,  # Student Level
        department,  # Department
        award_types,  # Award Type
        _,  # Program Length (in years)
        _,  # College
        cip_code,  # CIP Code
        _,  # CIP Description
        _,  # STEM
        _,  # Self Supporting
        _,  # Discontinued or Phasing Out
        _,  # Notes
    ) in rows:
        majors[isis_code] = MajorInfo(
            isis_code,
            title,
            department,
            cip_code[0:2] + "." + cip_code[2:],
            set(award_types.split(" ")) if award_types else set(),
        )
    return majors


_major_codes: Optional[Dict[str, MajorInfo]] = None


def major_codes():
    global _major_codes
    if _major_codes is None:
        _major_codes = major_rows_to_dict(
            read_csv_from(
                "./files/isis_major_code_list.xlsx - Major Codes.csv",
                "There is no `isis_major_code_list.xlsx - Major Codes.csv` file in the files/ folder. See the README for where to download it from.",
                strip=True,
            )[1:]
        )
    return _major_codes


if __name__ == "__main__":
    print(" ".join(major_plans(2019).keys()))
    # print(major_plans(2018)["AN26"].plans["SN"])
    # for term in range(15, 23):
    #     print(f"SP{term}: {prereqs(f'SP{term}')['MMW', '15']}")
    # print(prereqs("SP24")[("CSE", "12")])
