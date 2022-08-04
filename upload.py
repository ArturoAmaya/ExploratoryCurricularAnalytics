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

from contextlib import contextmanager
import os
from typing import Dict, Generator, Optional

from dotenv import load_dotenv  # type: ignore

from api import Session
from college_names import college_names
from output import MajorOutput
from parse import MajorInfo, major_codes, major_plans

Uploaded = Dict[str, int]

__all__ = ["MajorUploader"]

load_dotenv()


class MajorUploader(Session):
    def __init__(self) -> None:
        session = os.getenv("CA_SESSION")
        if session is None:
            raise EnvironmentError(
                f"There is no `CA_SESSION` environment variable defined. See the README to see how to set up `.env`."
            )
        super().__init__(session, os.getenv("AUTHENTICITY_TOKEN"))

    def upload_major(
        self,
        major: MajorInfo,
        organization_id: int,
        year: int,
        initials: str,
        log: bool = False,
    ) -> int:
        """
        Uploads the curriculum and all its college degree plans of the given major
        to the given organization.

        We're supposed to sign the CSV files with our initials, so `initials` is
        prepended to the CSV file names uploaded to Curricular Analytics.

        Set `log` to true to print a status message after every request, like when a
        CSV file is uploaded.
        """
        major_code = major.isis_code
        output = MajorOutput(major_plans(year)[major_code])
        self.upload_curriculum(
            organization_id,
            f"{year} {major_code}-{major.name}",
            year,
            (f"{initials}-Curriculum Plan-{major_code}.csv", output.output()),
        )
        if log:
            print(f"[{major_code}] Curriculum uploaded")
        curriculum_id = self.get_curricula(4, direction="desc")[0].curriculum_id()
        if log:
            print(
                f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
            )
        for college_code, college_name in college_names.items():
            if college_code not in output.plans.plans:
                continue
            self.upload_degree_plan(
                curriculum_id,
                f"{major_code}/{college_name}",
                (
                    f"SY-Degree Plan-{college_name}-{major_code}.csv",
                    output.output(college_code),
                ),
            )
            if log:
                print(f"[{major_code}] {college_name} degree plan uploaded")
        return curriculum_id

    def upload_major_json(
        self, major: MajorInfo, organization_id: int, year: int, log: bool = False
    ) -> int:
        """
        Identical to `upload_major`, but significantly slower due to the server
        seemingly taking longer to process it. No initials are required because they
        are only used to sign file names, and uploading a JSON does not involve file
        names.
        """
        major_code = major.isis_code
        output = MajorOutput(major_plans(year)[major_code])
        self.upload_curriculum(
            organization_id,
            f"{year} {major_code}-{major.name}",
            year,
            output.output_json(),
            major.cip_code,
        )
        if log:
            print(f"[{major_code}] Curriculum uploaded")
        curriculum_id = self.get_curricula(4, direction="desc")[0].curriculum_id()
        if log:
            print(
                f"[{major_code}] Curriculum URL: https://curricularanalytics.org/curriculums/{curriculum_id}"
            )
        for college_code, college_name in college_names.items():
            if college_code not in output.plans.plans:
                continue
            self.upload_degree_plan(
                curriculum_id,
                f"{major_code}/{college_name}",
                output.output_json(college_code),
            )
            if log:
                print(f"[{major_code}] {college_name} degree plan uploaded")
        return curriculum_id

    def edit_major(
        self,
        curriculum_id: int,
        major: MajorInfo,
        year: int,
        start_id: int = 1,
        log: bool = False,
    ) -> int:
        """
        Similar to `upload_major_json`, but instead edits an existing curriculum.
        """
        major_code = major.isis_code
        output = MajorOutput(major_plans(year)[major_code], start_id=start_id)
        self.edit_curriculum(curriculum_id, output.output_json())
        self.edit_curriculum_metadata(
            curriculum_id,
            name=f"{year} {major_code}-{major.name}",
            cip_code=major.cip_code,
        )
        if log:
            print(f"[{major_code}] Curriculum edited")
        plan_ids = self.get_degree_plans(curriculum_id)
        for college_code, college_name in college_names.items():
            plan_name = f"{major_code}/{college_name}"
            if college_code not in output.plans.plans:
                continue
            if plan_name in plan_ids:
                self.edit_degree_plan(
                    plan_ids[plan_name], output.output_json(college_code)
                )
                if log:
                    print(f"[{major_code}] {college_name} degree plan edited")
            else:
                self.upload_degree_plan(
                    curriculum_id, plan_name, output.output_json(college_code)
                )
                if log:
                    print(f"[{major_code}] {college_name} degree plan uploaded")
        return curriculum_id


@contextmanager
def track_uploaded_curricula(year: int) -> Generator[Uploaded, None, None]:
    URL_BASE = "https://curricularanalytics.org/curriculums/"
    curricula: Uploaded = {}
    try:
        with open(f"./files/uploaded{year}.yml") as file:
            for line in file.read().splitlines():
                major_code, curriculum_id = line.split(":", maxsplit=1)
                curriculum_id = curriculum_id.strip()
                if curriculum_id.startswith(URL_BASE):
                    curricula[major_code] = int(curriculum_id[len(URL_BASE) :])
    except FileNotFoundError:
        pass
    try:
        yield curricula
    finally:
        with open(f"./files/uploaded{year}.yml", "w") as file:
            for major_code in major_plans(year).keys():
                curriculum_id = curricula.get(major_code)
                if curriculum_id is None:
                    file.write(f"{major_code}:\n")
                else:
                    file.write(f"{major_code}: {URL_BASE}{curriculum_id}\n")


if __name__ == "__main__":
    from argparse import ArgumentParser

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

    parser = ArgumentParser(
        description="Automatically upload a major's curriculum and degree plans onto Curricular Analytics."
    )
    parser.add_argument("major_code", help="The ISIS code of the major to upload.")
    parser.add_argument(
        "--org",
        type=int,
        help="The ID of the Curricular Analytics organization to add the curriculum to. Default: $ORG_ID",
    )
    parser.add_argument("--year", type=int, help="The catalog year.")
    parser.add_argument(
        "--initials",
        help="Your initials, to sign the CSV file names. Default: $INITIALS",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Upload by JSON rather than by CSV files. Uploading by JSON is slower. Default: upload CSV files",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Whether to keep track of uploaded curricula in files/uploaded[year].yml. Default: don't keep track",
    )
    args = parser.parse_args()
    major_code: str = args.major_code
    if major_code not in major_codes():
        raise KeyError(f"{major_code} is not a major code that I know of.")
    org_id: Optional[int] = args.org
    if org_id is None:
        org_id = int(get_env("ORG_ID"))
    year: Optional[int] = args.year
    if year is None:
        raise ValueError("Year is required.")
    initials: Optional[str] = args.initials
    if initials is None:
        initials = get_env("INITIALS")
    upload = lambda: (
        MajorUploader().upload_major_json(
            major_codes()[major_code], org_id, year, log=True
        )
        if args.json
        else MajorUploader().upload_major(
            major_codes()[major_code], org_id, year, initials, log=True
        )
    )
    if args.track:
        with track_uploaded_curricula(year) as curricula:
            if major_code in curricula:
                raise KeyError(f"{major_code} already uploaded")
            curricula[major_code] = upload()
    else:
        upload()
