"""
Parses the prerequisite and academic plan CSV files into objects for easier
manipulation.

Exports:
    `prereqs`, a dictionary mapping from a subject code-number tuple to a list
    of prerequisites, which are each lists of possible course codes to satisfy
    the requirement.

    `majors`, a dictionary mapping from ISIS major codes to `Major` objects,
    which contains a dictionary mapping college codes to `Plan`s, which have a
    list of list of `PlannedCourse`s for each quarter.

    `major_codes`, a dictionary mapping from ISIS major codes to `MajorInfo`
    objects, which contains data from the ISIS major codes spreadsheet.
"""

from typing import Dict, List, Literal, Optional, Tuple

Course = Tuple[str, str]
Prerequisite = Tuple[Course, bool]


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
            # NOTE: Currently doesn't deal with backslashes
            field = field[1:-1]
        return field.strip() if strip else field

    try:
        with open(path, "r") as file:
            for line in file.read().splitlines():
                row: List[str] = []
                rows.append(row)
                last_index: int = 0
                in_quotes: bool = False
                ignore_next: bool = False  # For backslashes in quotes
                for i, char in enumerate(line):
                    if in_quotes:
                        if ignore_next:
                            ignore_next = False
                        elif char == '"':
                            in_quotes = False
                        elif char == "\\":
                            ignore_next = True
                    else:
                        if char == '"':
                            in_quotes = True
                        elif char == ",":
                            row.append(parse_field(line[last_index:i]))
                            last_index = i + 1
                row.append(parse_field(line[last_index:]))
    except FileNotFoundError as e:
        raise e if not_found_msg is None else FileNotFoundError(not_found_msg)
    return rows


def prereq_rows_to_dict(
    rows: List[List[str]],
) -> Dict[Course, List[List[Prerequisite]]]:
    """
    Converts prerequisite rows from a CSV to a dictionary mapping between
    courses and the prerequisites.

    The dictionary values are lists of lists. The outer list is a list of
    requirements, like an AND, while each inner list is a list of possible
    courses to satisfy the requirement, like an OR.
    """
    prereqs: Dict[Course, List[List[Prerequisite]]] = {}
    for subject, number, prereq_id, pre_sub, pre_num, allow_concurrent in rows:
        # NOTE: Currently ignoring "Allow concurrent registration?" because I don't
        # know what to do with it
        course: Course = subject, number
        prereq: Prerequisite = (pre_sub, pre_num), allow_concurrent == "Y"
        if course not in prereqs:
            prereqs[course] = []
        index = int(prereq_id) - 1
        while len(prereqs[course]) <= index:
            prereqs[course].append([])
        # Could probably include the allow concurrent registration info here
        prereqs[course][index].append(prereq)
    return prereqs


class PlannedCourse:
    """
    Represents a course in an academic plan.
    """

    course: str
    units: float
    type: Literal["COLLEGE", "DEPARTMENT"]
    overlaps_ge: bool

    def __init__(
        self,
        course: str,
        units: float,
        type: Literal["COLLEGE", "DEPARTMENT"],
        overlaps_ge: bool,
    ) -> None:
        self.course = course
        self.units = units
        self.type = type
        self.overlaps_ge = overlaps_ge

    def __repr__(self) -> str:
        return f"PlannedCourse(course={repr(self.course)}, units={repr(self.units)}, type={repr(self.type)}, overlaps_ge={repr(self.overlaps_ge)})"


class Plan:
    """
    Represents a college-specific academic plan. Can be used to create degree
    plans for Curricular Analytics.
    """

    quarters: List[List[PlannedCourse]]

    def __init__(self, quarters: Optional[List[List[PlannedCourse]]] = None) -> None:
        # https://stackoverflow.com/a/33990699
        self.quarters = [[] for _ in range(12)] if quarters is None else quarters

    def __repr__(self) -> str:
        return f"Plan(quarters={repr(self.quarters)})"


class Major:
    """
    Represents a major. Contains plans for each college.

    To get the plan for a specific college, use the two-letter college code. For
    example, `plans["FI"]` contains the academic plan for ERC (Fifth College).
    """

    department: str
    major: str
    plans: Dict[str, Plan]

    def __init__(
        self, department: str, major: str, plans: Optional[Dict[str, Plan]] = None
    ) -> None:
        self.department = department
        self.major = major
        self.plans = {} if plans is None else plans

    def curriculum(self, college: str = "RE") -> Plan:
        """
        Creates an academic plan with college-specific courses removed. Can be
        used to create a curriculum for Curricular Analytics.

        The `overlaps_ge` attribute for these courses should be ignored (because
        there is no college whose GEs the course overlaps with).

        Assumes that the department plans are the same for all colleges. It
        might be worth checking if that's actually the case. By default, it
        arbitrarily uses Revelle's college plan, but you can specify a college
        code in `college` to base the degree plan off a different college.
        """
        # Arbitrarily using Revelle
        return Plan(
            [
                [
                    course
                    for course in quarter
                    if course.type == "DEPARTMENT" or course.overlaps_ge
                ]
                for quarter in self.plans[college].quarters
            ]
        )

    def __repr__(self) -> str:
        return f"Major(department={repr(self.department)}, major={repr(self.major)}, plans={repr(self.plans)})"


def plan_rows_to_dict(rows: List[List[str]]) -> Dict[str, Major]:
    """
    Converts the academic plans CSV rows into a dictionary of major codes to
    `Major` objects.
    """
    majors: Dict[str, Major] = {}
    for (
        dept,  # Department
        major,  # Major
        college,  # College
        course,  # Course
        units,  # Units
        c_type,  # Course Type
        overlap,  # GE/Major Overlap
        _,  # Start Year
        year,  # Year Taken
        qtr,  # Quarter Taken
        _,  # Term Taken
    ) in rows:
        if major not in majors:
            majors[major] = Major(dept, major)
        if college not in majors[major].plans:
            majors[major].plans[college] = Plan()
        quarter = (int(year) - 1) * 3 + int(qtr) - 1
        if c_type != "COLLEGE" and c_type != "DEPARTMENT":
            raise TypeError('Course type is neither "COLLEGE" nor "DEPARTMENT"')
        majors[major].plans[college].quarters[quarter].append(
            PlannedCourse(course, float(units), c_type, overlap == "Y")
        )
    return majors


class MajorInfo:
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

    def __init__(self, isis: str, description: str, department: str, cip: str) -> None:
        self.isis_code = isis
        self.name = description
        self.department = department
        self.cip_code = cip


def major_rows_to_dict(rows: List[List[str]]) -> Dict[str, MajorInfo]:
    majors: Dict[str, MajorInfo] = {}
    for (
        _,  # Previous Local Code
        _,  # UCOP Major Code (CSS)
        isis,  # ISIS Major Code
        _,  # Major Abbreviation
        description,  # Major Description
        _,  # Diploma Title
        _,  # Start Term
        _,  # End Term
        _,  # Student Level
        department,  # Department
        _,  # Award Type
        _,  # Program Length (in years)
        _,  # College
        cip,  # CIP Code
        _,  # CIP Description
        _,  # STEM
        _,  # Self Supporting
        _,  # Discontinued or Phasing Out
        _,  # Notes
    ) in rows:
        majors[isis] = MajorInfo(isis, description, department, cip)
    return majors


prereqs = prereq_rows_to_dict(
    read_csv_from(
        "./files/prereqs.csv",
        "There is no `prereqs.csv` file in the files/ folder. See the README for where to download it from.",
        strip=True,
    )[1:]
)

majors = plan_rows_to_dict(
    read_csv_from(
        "./files/academic_plans.csv",
        "There is no `academic_plans.csv` file in the files/ folder. See the README for where to download it from.",
        strip=True,
    )[1:]
)

major_codes = major_rows_to_dict(
    read_csv_from(
        "./files/isis_major_code_list.xlsx - Major Codes.csv",
        "There is no `isis_major_code_list.xlsx - Major Codes.csv` file in the files/ folder. See the README for where to download it from.",
        strip=True,
    )[1:]
)

if __name__ == "__main__":
    print(prereqs["CAT", "1"])
    print(majors["CS26"].curriculum())
