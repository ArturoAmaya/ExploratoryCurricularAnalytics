"""
Automatically uploads a curriculum and each college's degree plan to Curricular
Analytics.

To authenticate yourself, it uses the `AUTHENTICITY_TOKEN` and `CA_SESSION`
environment variables. See the README for how to get them.

Exports:
    `upload_major`, which takes a major code, the organization ID, the catalog
    year, and your initials. It creates and uploads the curriculum and degree
    plans for the major to the organization on Curricular Analytics. Your
    initials are used to sign the CSV file names.
"""

import json
import os
import re
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv  # type: ignore

from college_names import college_names
from departments import departments
from output import MajorOutput
from parse import MajorInfo, major_codes

__all__ = ["upload_major"]

load_dotenv()


def get_env(name: str) -> str:
    """
    Get an environment variable, and if it's not set, then tell the user to set
    up their `.env` file.
    """
    value = os.getenv(name)
    if value is None:
        raise EnvironmentError(
            f"There is no `{name}` environment variable defined. See the README to see how to set up `.env`."
        )
    return value


authenticity_token = get_env("AUTHENTICITY_TOKEN")
session = get_env("CA_SESSION")

BOUNDARY = "BOUNDARY"
LINE = b"\r\n"


def post_form(
    url: str,
    form: Dict[str, Union[str, Tuple[str, bytes]]],
) -> None:
    """
    Submits an HTML form on Curricular Analytics with a POST request. The
    request body is `multipart/form-data`, so it can contain files.

    `url` is the URL that the form posts to (NOT the URL of the page that the
    form is on). `form` contains a dictionary mapping field names (i.e. the
    `name` attribute of the `<input />` elements) to string values or a tuple
    with a file name and the contents of the file.

    Handles authentication (includes the `Cookie` header based on the
    `CA_SESSION` environment variable) and identifies and raises errors for when
    the session or form's authenticity token are invalid.
    """
    body: bytearray = bytearray()
    for name, value in form.items():
        body += f"--{BOUNDARY}".encode("utf-8")
        body += LINE
        if type(value) is str:
            body += f'Content-Disposition: form-data; name="{name}"'.encode("utf-8")
            body += LINE
            body += LINE
            body += value.encode("utf-8")
            body += LINE
        elif type(value) is tuple:
            file_name, content = value
            body += f'Content-Disposition: form-data; name="{name}"; filename="{file_name}"'.encode(
                "utf-8"
            )
            body += LINE
            body += b"Content-Type: application/octet-stream"
            body += LINE
            body += LINE
            body += content
            body += LINE
    body += f"--{BOUNDARY}--".encode("utf-8")
    body += LINE
    try:
        with urlopen(
            Request(
                url,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={BOUNDARY}",
                    "Cookie": f"_curricularanalytics_session={session}",
                },
                data=body,
                method="POST",
            )
        ) as response:
            if response.url == "https://curricularanalytics.org/users/sign_in":
                raise RuntimeError(
                    "Curricular Analytics isn't recognizing your `CA_SESSION` environment variable. Could you try getting the session cookie again? See the README for how."
                )
    except HTTPError as error:
        raise RuntimeError(
            "Curricular Analytics doesn't seem to accept your `AUTHENTICITY_TOKEN` environment variable. Could you try getting a new one? See the README for how."
        ) if error.code == 422 else error


def upload_curriculum(
    organization_id: int, name: str, year: int, file_name: str, csv: str
) -> None:
    """
    Creates a new curriculum under the given organization.
    """
    post_form(
        "https://curricularanalytics.org/curriculums",
        {
            "authenticity_token": authenticity_token,
            "curriculum[name]": name,
            "curriculum[organization_id]": str(organization_id),
            "curriculum[catalog_year]": str(year),
            "curriculum[cip]": "",  # Curricular Analytics will get it from the CSV
            "curriculum[curriculum_file]": (file_name, csv.encode("utf-8")),
            "entry_method": "csv_file",
            "curriculum_json": "",
            "commit": "Save",
        },
    )


def upload_degree_plan(curriculum_id: int, name: str, file_name: str, csv: str) -> None:
    """
    Creates a new degree plan under the given curriculum.
    """
    post_form(
        "https://curricularanalytics.org/degree_plans",
        {
            "authenticity_token": authenticity_token,
            "degree_plan[name]": name,
            "degree_plan[curriculum_id]": str(curriculum_id),
            "degree_plan[degree_plan_file]": (file_name, csv.encode("utf-8")),
            "entry_method": "csv_file",
            "curriculum_json": "",
            "commit": "Save",
        },
    )


class CurriculumEntry(NamedTuple):
    """
    A row in the table listing the user's curricula on Curricular Analytics.
    """

    raw_name: str
    raw_organization: str
    cip_code: str
    year: int
    date_created: str

    def curriculum_id(self) -> int:
        """
        Get the ID of the curriculum from its URL in the "Name" column
        (`raw_name`).
        """
        match = re.match(r'<a href="/curriculums/(\d+)', self.raw_name)
        if match is None:
            raise ValueError(
                f"The name of the curriculum entry `{self.raw_name}` doesn't seem to be a link."
            )
        return int(match.group(1))


def get_curricula(
    sort_by: int,
    direction: Literal["desc", "asc"] = "asc",
    offset: int = 0,
    items: int = 1,
    search: str = "",
) -> List[CurriculumEntry]:
    """
    Get the user's curricula on Curricular Analytics. This is equivalent to the
    table the user sees at https://curricularanalytics.org/curriculums.

    Used by `upload_major` to get the ID of the most recently created
    curriculum.

    `sort_by` should be the index of the column to sort by, and `direction` is
    whether it should be sorted in ascending (`asc`) or descending (`desc`)
    order. For example, to get the most recent curricula, the creation date is
    the fifth column (index 4), and to put the latest date first, sort it in
    descending order.

    ```py
    curricula = get_curricula(4, 'desc')
    ```

    `offset` is the index into the results to start returning curricula, while
    `items` is the maximum number of curricula to get. `search` filters the list
    of curricula by a keyword.
    """
    params = urlencode(
        {
            "order[0][column]": sort_by,
            "order[0][dir]": direction,
            "start": offset,
            "length": items,
            "search[value]": search,
        }
    )
    try:
        with urlopen(
            Request(
                "https://curricularanalytics.org/curriculums?" + params,
                headers={
                    "Accept": "application/json",
                    "Cookie": f"_curricularanalytics_session={session}",
                },
            )
        ) as response:
            data = json.load(response)["data"]
            return [
                CurriculumEntry(
                    raw_name, raw_organization, cip_code, year, date_created
                )
                for raw_name, raw_organization, cip_code, year, date_created, _ in data
            ]
    except HTTPError as error:
        raise RuntimeError(
            "Curricular Analytics isn't recognizing your `CA_SESSION` environment variable. Could you try getting the session cookie again? See the README for how."
        ) if error.code == 401 else error


def upload_major(
    major: MajorInfo, organization_id: int, year: int, initials: str, log: bool = False
) -> None:
    """
    Uploads the curriculum and all its college degree plans of the given major
    to the given organization.

    We're supposed to sign the CSV files with our initials, so `initials` is
    prepended to the CSV file names uploaded to Curricular Analytics.

    Set `log` to true to print a status message after every request, like when a
    CSV file is uploaded.
    """
    major_code = major.isis_code
    output = MajorOutput(major_code)
    upload_curriculum(
        organization_id,
        f"{major_code}-{departments[major.department]}",
        year,
        f"{initials}-Curriculum Plan-{major_code}.csv",
        output.output(),
    )
    if log:
        print(f"[{major_code}] Curriculum uploaded")
    curriculum_id = get_curricula(4, direction="desc")[0].curriculum_id()
    if log:
        print(
            f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
        )
    for college_code, college_name in college_names.items():
        if college_code not in output.plans.plans:
            continue
        upload_degree_plan(
            curriculum_id,
            f"{major_code}/{college_name}",
            f"SY-Degree Plan-{college_name}-{major_code}.csv",
            output.output(college_code),
        )
        if log:
            print(f"[{major_code}] {college_name} degree plan uploaded")


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Automatically upload a major's curriculum and degree plans onto Curricular Analytics."
    )
    parser.add_argument("major_code", help="The ISIS code of the major to upload.")
    parser.add_argument(
        "--org",
        type=int,
        help="The ID of the Curricular Analytics organization to add the curriculum to. Defaults to the ORG_ID environment variable.",
    )
    parser.add_argument(
        "--year", type=int, help="The catalog year. Defaults to 2021.", default=2021
    )
    parser.add_argument(
        "--initials",
        help="Your initials, to sign the CSV file names. Defaults to the INITIALS environment variable.",
    )
    args = parser.parse_args()
    major_code: str = args.major_code
    if major_code not in major_codes:
        raise KeyError(f"{major_code} is not a major code that I know of.")
    org_id: Optional[int] = args.org
    if org_id is None:
        org_id = int(get_env("ORG_ID"))
    year: int = args.year
    initials: Optional[str] = args.initials
    if initials is None:
        initials = get_env("INITIALS")
    upload_major(major_codes[major_code], org_id, year, initials, log=True)
