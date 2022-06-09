import os
from typing import Dict, Tuple, Union
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv  # type: ignore

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
):
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


post_form(
    "https://curricularanalytics.org/degree_plans",
    {
        "authenticity_token": authenticity_token,
        "degree_plan[name]": "apple cider",
        "degree_plan[curriculum_id]": "19353",
        "entry_method": "csv_file",
        "degree_plan[degree_plan_file]": ("billy", b""),
        "curriculum_json": "",
        "commit": "Save",
    },
    headers={"cookie": f"_curricularanalytics_session={session}"},
)
