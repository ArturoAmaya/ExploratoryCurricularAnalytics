"""
Parses the prerequisite and academic plan CSV files into objects for easier
manipulation.

Exports:
    `prereqs`, a dictionary mapping from a subject code-number tuple to a list
    of prerequisites, which are each lists of possible course codes to satisfy
    the requirement.
"""


from typing import Dict, List, Optional, Tuple

Course = Tuple[str, str]


def read_csv_from(
    path: str, not_found_msg: Optional[str], strip: Optional[bool] = False
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


prereq_rows = read_csv_from(
    "./files/prereqs.csv",
    "There is no prereqs.csv file in the files/ folder. Have you downloaded it from the Google Drive folder?",
    strip=True,
)
prereqs: Dict[Course, List[List[Course]]] = {}
for subject, number, prereq_id, pre_sub, pre_num, _ in prereq_rows[1:]:
    # NOTE: Currently ignoring "Allow concurrent registration?" because I don't
    # know what to do with it
    course: Course = subject, number
    prereq: Course = pre_sub, pre_num
    if course not in prereqs:
        prereqs[course] = []
    index = int(prereq_id) - 1
    while len(prereqs[course]) <= index:
        prereqs[course].append([])
    # Could probably include the allow concurrent registration info here
    prereqs[course][index].append(prereq)


academic_plans = read_csv_from(
    "./files/academic_plans.csv",
    "There is no academic_plans.csv file in the files/ folder. Have you downloaded it from the Google Drive folder?",
)
