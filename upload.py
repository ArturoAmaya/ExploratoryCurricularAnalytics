from typing import Dict, List, Union
from urllib.request import Request, urlopen

BOUNDARY = "BOUNDARY"
LINE = b"\r\n"


def post_form(
    url: str, form: Dict[str, Union[str, bytes]], headers: Dict[str, str] = {}
):
    body = bytearray()
    for name, value in form.items():
        body += [
            f"--{BOUNDARY}",
            f'Content-Disposition: form-data; name="{name}"',
        ]
        if type(value) is str:
            body_lines += ["", value]
    body_lines += [f"--{BOUNDARY}", ""]
    urlopen(
        Request(
            url,
            headers={
                "Content-Type": f"multipart/form-data; boundary={BOUNDARY}",
                **headers,
            },
            data=body,
            method="POST",
        )
    )


post_form(
    "https://curricularanalytics.org/degree_plans",
    {
        "authenticity_token": "wxkzi7cRlgNU3o6Y5TauF6kGmVSvZCSEmkXrz/M8/jpEUVobkw1JyHYWGYxXEcJRbVvNIBGIeDe1eRlwEd5Tvw==",
        "degree_plan[name]": "a",
        "degree_plan[curriculum_id]": "19353",
        "entry_method": "csv_file",
        "degree_plan[degree_plan_file]": "(binary)",
        "curriculum_json": "",
        "commit": "Save",
    },
)
