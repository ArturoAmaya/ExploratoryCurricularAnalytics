import json
import os
import re
from typing import Dict, List, Literal, NamedTuple, Optional, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv  # type: ignore

from output import college_names, output
from parse import MajorInfo, major_codes

load_dotenv()

authenticity_token = os.getenv("AUTHENTICITY_TOKEN")
if authenticity_token is None:
    raise EnvironmentError(
        "There is no `AUTHENTICITY_TOKEN` environment variable defined. See the README to see how to set up `.env`."
    )
session = os.getenv("CA_SESSION")
if session is None:
    raise EnvironmentError(
        "There is no `CA_SESSION` environment variable defined. See the README to see how to set up `.env`."
    )

BOUNDARY = "BOUNDARY"
LINE = b"\r\n"


def post_form(
    url: str,
    form: Dict[str, Union[str, Tuple[str, bytes]]],
    headers: Dict[str, str] = {},
) -> None:
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
                    **headers,
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


class CurriculumEntry(NamedTuple):
    raw_name: str
    raw_organization: str
    cip_code: str
    year: int
    date_created: str

    def curriculum_id(self) -> int:
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


def upload_degree_plan(curriculum_id: int, name: str, file_name: str, csv: str) -> None:
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
        headers={"Cookie": f"_curricularanalytics_session={session}"},
    )


def upload_curriculum(
    organization_id: int, name: str, year: int, file_name: str, csv: str
) -> None:
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
        headers={"Cookie": f"_curricularanalytics_session={session}"},
    )


def get_csv(major_code: str, college: Optional[str] = None) -> str:
    csv = ""
    for line in output(major_code, college):
        csv += line
    return csv


def upload_major(
    major: MajorInfo, organization_id: int, year: int, initials: str, log: bool = False
) -> None:
    major_code = major.isis_code
    upload_curriculum(
        organization_id,
        f"{major_code}-{major.name}",  # TODO: Get department name (per instructions)
        year,
        f"{initials}-Curriculum Plan-{major_code}.csv",
        get_csv(major_code),
    )
    if log:
        print(f"[{major_code}] Curriculum uploaded")
    curriculum_id = get_curricula(4, direction="desc")[0].curriculum_id()
    if log:
        print(
            f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
        )
    for college_code, college_name in college_names.items():
        upload_degree_plan(
            curriculum_id,
            f"{major_code}/{college_name}",
            f"SY-Degree Plan-{college_name}-{major_code}.csv",
            get_csv(major_code, college_code),
        )
        if log:
            print(f"[{major_code}] {college_name} degree plan uploaded")


if __name__ == "__main__":
    upload_major(major_codes["CR25"], 19409, 2022, "SY", log=True)
