import json
import re
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Tuple, Union
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HOST = "https://curricularanalytics.org"


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


class Session:
    session: str
    authenticity_token: Optional[str]

    def __init__(self, session: str, authenticity_token: Optional[str] = None) -> None:
        """
        `authenticity_token` is optional because it can get one by itself, but
        you can help save a request by providing your own.
        """
        self.session = session
        self.authenticity_token = authenticity_token

    def get_auth_token(self) -> str:
        if self.authenticity_token is None:
            return "TODO"
        else:
            return self.authenticity_token

    def get_json(self, path: str) -> Any:
        try:
            with urlopen(
                Request(
                    HOST + path,
                    headers={
                        "Accept": "application/json",
                        "Cookie": f"_curricularanalytics_session={self.session}",
                    },
                )
            ) as response:
                return json.load(response)
        except HTTPError as error:
            raise RuntimeError(
                "Curricular Analytics isn't recognizing your `CA_SESSION` environment variable. Could you try getting the session cookie again? See the README for how."
            ) if error.code == 401 else error

    BOUNDARY = "BOUNDARY"
    LINE = b"\r\n"

    def post_form(
        self,
        path: str,
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
            body += f"--{Session.BOUNDARY}".encode("utf-8")
            body += Session.LINE
            if type(value) is str:
                body += f'Content-Disposition: form-data; name="{name}"'.encode("utf-8")
                body += Session.LINE
                body += Session.LINE
                body += value.encode("utf-8")
                body += Session.LINE
            elif type(value) is tuple:
                file_name, content = value
                body += f'Content-Disposition: form-data; name="{name}"; filename="{file_name}"'.encode(
                    "utf-8"
                )
                body += Session.LINE
                body += b"Content-Type: application/octet-stream"
                body += Session.LINE
                body += Session.LINE
                body += content
                body += Session.LINE
        body += f"--{Session.BOUNDARY}--".encode("utf-8")
        body += Session.LINE
        try:
            with urlopen(
                Request(
                    HOST + path,
                    headers={
                        "Content-Type": f"multipart/form-data; boundary={Session.BOUNDARY}",
                        "Cookie": f"_curricularanalytics_session={self.session}",
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
        self, organization_id: int, name: str, year: int, file_name: str, csv: str
    ) -> None:
        """
        Creates a new curriculum under the given organization.
        """
        self.post_form(
            "https://curricularanalytics.org/curriculums",
            {
                "authenticity_token": self.get_auth_token(),
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

    def upload_degree_plan(
        self, curriculum_id: int, name: str, file_name: str, csv: str
    ) -> None:
        """
        Creates a new degree plan under the given curriculum.
        """
        self.post_form(
            "https://curricularanalytics.org/degree_plans",
            {
                "authenticity_token": self.get_auth_token(),
                "degree_plan[name]": name,
                "degree_plan[curriculum_id]": str(curriculum_id),
                "degree_plan[degree_plan_file]": (file_name, csv.encode("utf-8")),
                "entry_method": "csv_file",
                "curriculum_json": "",
                "commit": "Save",
            },
        )

    def get_curricula(
        self,
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
        data = self.get_json("/curriculums?" + params)["data"]
        return [
            CurriculumEntry(raw_name, raw_organization, cip_code, year, date_created)
            for raw_name, raw_organization, cip_code, year, date_created, _ in data
        ]
