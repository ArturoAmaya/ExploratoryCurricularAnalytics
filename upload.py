from typing import Dict, Tuple, Union
from urllib.request import Request, urlopen

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
        print(response.read())


post_form(
    "https://curricularanalytics.org/degree_plans",
    {
        "authenticity_token": "NO.",
        "degree_plan[name]": "apple cider",
        "degree_plan[curriculum_id]": "19353",
        "entry_method": "csv_file",
        "degree_plan[degree_plan_file]": ("billy", b""),
        "curriculum_json": "",
        "commit": "Save",
    },
    headers={"cookie": "CENSORED I FOOL"},
)
