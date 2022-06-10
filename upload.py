import os
from typing import Dict, Tuple, Union
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv  # type: ignore

from output import output

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
        headers={"cookie": f"_curricularanalytics_session={session}"},
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
        headers={"cookie": f"_curricularanalytics_session={session}"},
    )


if __name__ == "__main__":
    csv = ""
    for line in output("ES26"):
        csv += line
    upload_curriculum(
        19409,
        "ES26-Environmental Systems",
        2022,
        "SY-Curriculum Plan-ES26.csv",
        csv,
    )
