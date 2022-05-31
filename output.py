"""
handles output in happy csv format
"""

from typing import Callable, List, Optional

from .parse import Major, major_codes

OutputFunc = Callable[[str], None]


INSTITUTION = "University of California, San Diego"
SYSTEM_TYPE = "Quarter"


class Outputter:
    columns: int
    output: OutputFunc

    def __init__(self, columns: int, output: OutputFunc) -> None:
        self.columns = columns
        self.output = output

    def output_row(self, row: List[str]) -> None:
        # Output a row in CSV, quoting fields as needed and adding empty records
        # to fill up the row
        # NOTE: Only quotes a field if it contains a comma
        self.output(
            ",".join(
                [f'"{field}"' if "," in field else field for field in row]
                + [""] * (self.columns - len(row))
            )
            + "\n"
        )

    def output_header(
        self,
        curriculum: str = "",
        degree_plan: Optional[str] = None,
        institution: str = "",
        degree_type: str = "",
        system_type: str = "",
        cip: str = "",
    ) -> None:
        """
        Outputs the header for the CSV file. See Curricular Analytics'
        documentation for the CSV header format:
        https://curricularanalytics.org/files.
        """
        self.output_row(["Curriculum", curriculum])
        if degree_plan is not None:
            self.output_row(["Degree Plan", degree_plan])
        self.output_row(["Institution", institution])
        self.output_row(["Degree Type", degree_type])
        self.output_row(["System Type", system_type])
        self.output_row(["CIP", cip])
        self.output_row(["Courses"])


def output_curriculum(major: Major, output: OutputFunc) -> None:
    """
    wow
    """
    outputter = Outputter(10, output)
    major_info = major_codes[major.major]
    outputter.output_header(
        curriculum=major_info.name,
        institution=INSTITUTION,
        degree_type="BS",  # TEMP
        system_type=SYSTEM_TYPE,
        cip=major_info.cip_code,
    )
    # TODO
