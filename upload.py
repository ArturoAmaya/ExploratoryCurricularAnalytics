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

import os
from typing import Optional

from dotenv import load_dotenv  # type: ignore

from api import Session
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


session = Session(get_env("CA_SESSION"), get_env("AUTHENTICITY_TOKEN"))


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
    session.upload_curriculum(
        organization_id,
        f"{major_code}-{departments[major.department]}",
        year,
        (f"{initials}-Curriculum Plan-{major_code}.csv", output.output()),
    )
    if log:
        print(f"[{major_code}] Curriculum uploaded")
    curriculum_id = session.get_curricula(4, direction="desc")[0].curriculum_id()
    if log:
        print(
            f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
        )
    for college_code, college_name in college_names.items():
        if college_code not in output.plans.plans:
            continue
        session.upload_degree_plan(
            curriculum_id,
            f"{major_code}/{college_name}",
            (
                f"SY-Degree Plan-{college_name}-{major_code}.csv",
                output.output(college_code),
            ),
        )
        if log:
            print(f"[{major_code}] {college_name} degree plan uploaded")


def upload_major_json(
    major: MajorInfo, organization_id: int, year: int, log: bool = False
) -> None:
    """
    Identical to `upload_major`, but significantly slower due to the server
    seemingly taking longer to process it. No initials are required because they
    are only used to sign file names, and uploading a JSON does not involve file
    names.
    """
    major_code = major.isis_code
    output = MajorOutput(major_code)
    session.upload_curriculum(
        organization_id,
        f"{major_code}-{departments[major.department]}",
        year,
        output.output_json(),
        major.cip_code,
    )
    if log:
        print(f"[{major_code}] Curriculum uploaded")
    curriculum_id = session.get_curricula(4, direction="desc")[0].curriculum_id()
    if log:
        print(
            f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
        )
    for college_code, college_name in college_names.items():
        if college_code not in output.plans.plans:
            continue
        session.upload_degree_plan(
            curriculum_id,
            f"{major_code}/{college_name}",
            output.output_json(college_code),
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
