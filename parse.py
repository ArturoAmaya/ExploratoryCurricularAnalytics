"""
Parses the prerequisite and academic plan CSV files into objects for easier
manipulation.
"""


from typing import List, Optional


def read_csv_from(path: str, not_found_msg: Optional[str]) -> List[List[str]]:
    rows: List[List[str]] = []
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
                            element: str = line[last_index:i]
                            # NOTE: Currently doesn't deal with backslashes
                            row.append(
                                element[1:-1]
                                if len(element) > 0 and element[0] == '"'
                                else element
                            )
                            last_index = i + 1
                element: str = line[last_index:]
                # NOTE: Currently doesn't deal with backslashes
                row.append(
                    element[1:-1] if len(element) > 0 and element[0] == '"' else element
                )
    except FileNotFoundError as e:
        raise e if not_found_msg is None else FileNotFoundError(not_found_msg)
    return rows


prereqs = read_csv_from(
    "./files/prereqs.csv",
    "There is no prereqs.csv file in the files/ folder. Have you downloaded it from the Google Drive folder?",
)
academic_plans = read_csv_from(
    "./files/academic_plans.csv",
    "There is no academic_plans.csv file in the files/ folder. Have you downloaded it from the Google Drive folder?",
)
