# Hi!
If you're here for newer stuff, head on over to [Sean's fork of this repo](https://github.com/SheepTester-forks/ExploratoryCurricularAnalytics). It's newer, faster, snazzier and has a lot more features as well as executive decisions and bugfixes we've made since Jun 2022 about parsing plans. If you just want the original parsing stuff or want to get started doing this at you own institution, check here.

## Setup

[`parse.py`](parse.py) expects certain files in the `files/` directory. Download them from our shared Google Drive folder.

- [**`academic_plans_fa12.csv`**](https://drive.google.com/file/d/1SMNCi_UD3NoIyUt8TidpPOWha_pOx3il/view),
  containing degree plans for every year, major, and college combination since
  fall 2012 created by college advisors painstakingly cross-referencing major
  and college requirements to manually design plans for every major, so there
  are some human errors. These plans are publicly available at
  [plans.ucsd.edu](https://plans.ucsd.edu/).

  We use this to create degree plans and curriculum for every major to upload to
  [Curricular Analytics](https://curricularanalytics.org/).

  If others want to adapt our code for their university, here is a preview of
  the first two rows to show what we were dealing with.

  | Department | Major | College | Course | Units | Course Type | GE/Major Overlap | Start Year | Year Taken | Quarter Taken | Term Taken |
  | ---------- | ----- | ------- | ------ | ----- | ----------- | ---------------- | ---------- | ---------- | ------------- | ---------- |
  | ANTHROPOLO | AN27  | SI      | ANTH 1 | 4.0   | DEPARTMENT  | N                | 2012       | 1          | 1             | FA12       |

  - `Major` is an [ISIS major
    code](https://blink.ucsd.edu/instructors/academic-info/majors/major-codes.html).

  - `College` is a two-letter code for a UCSD college.

    | Code | Name                                               |
    | ---- | -------------------------------------------------- |
    | RE   | Revelle                                            |
    | MU   | Muir                                               |
    | TH   | Marshall (formerly Third)                          |
    | WA   | Warren                                             |
    | FI   | ERC (formerly Fifth)                               |
    | SI   | Sixth                                              |
    | SN   | Seventh                                            |
    | DP   | Appears in the file, but we're not sure what it is |

    Generally speaking, every major has a plan for every college. However, there
    are exceptions, usually for weird majors that aren't actually 4-year plans
    (e.g. only Revelle has plans for undeclared "majors").

  - `Course` is a **manually-written** description of a course. It's usually the
    course subject and number, but it can also be a phrase like "CSE Elective"
    or list alternatives like "MATH 10A/20A." Human error makes parsing this
    difficult; see [`parse_course_name`](./parse_course_name.py) for an attempt.

  - `Course Type` is either `COLLEGE` or `DEPARTMENT`. When `GE/Major Overlap`
    is `Y` (a course satisfies both major and college requirements), `Course Type` can still be either `COLLEGE` or `DEPARTMENT`.

    To get a curriculum (the major requirements) from a plan, we only keep
    courses with a `Course Type` of `DEPARTMENT` _or_ a `GE/Major Overlap` of
    `Y`.

    They do not provide a plan with only major requirements. In #14 it seems
    removing college-specific courses from Marshall (TH)'s degree plan tends to
    produce the most compatible results for other colleges, so we base curricula
    off of Marshall.

  - `Start Year` indicates the year that the plan is for. For example, a student
    who enrolls at UCSD in fall 2019 should follow the plan with a `Start Year`
    of 2019.

  Some but not all degree plans put courses in a summer quarter (with a `Term Taken` of `SUxx`) even though they're not supposed to.

- [**`prereqs_fa12.csv`**](https://drive.google.com/file/d/19oVI16mmhDIclyj6p3GMlxTMPDRNIcHw/view),
  containing every course and their prerequisites for every quarter since fall 2012.

  We use this to add prerequisite and corequisite relationships between courses
  in the degree plans for [Curricular
  Analytics](https://curricularanalytics.org/).

  Here are some sample rows from the CSV file.

  | Term Code | Term ID | Course ID | Course Subject Code | Course Number | Prereq Sequence ID | Prereq Course ID | Prereq Subject Code | Prereq Course Number | Prereq Minimum Grade Priority | Prereq Minimum Grade | Allow concurrent registration |
  | --------- | ------- | --------- | ------------------- | ------------- | ------------------ | ---------------- | ------------------- | -------------------- | ----------------------------- | -------------------- | ----------------------------- |
  | FA12      | 4550    | AIP197    | AIP                 | 197           |                    |                  |                     |                      |                               |                      |
  | FA12      | 4550    | ANAR144   | ANAR                | 144           | 001                | ANTH3            | ANTH                | 3                    | 600                           | P                    | Y                             |

  Some courses do not have prerequisites, so they will have a single row with
  empty fields after `Course Number`.

  For courses with prerequisites, they will have a row for every prerequisite
  course. `Prereq Sequence ID` is a natural number, and of the prerequisites
  with the same `Prereq Sequence ID`, only one course is needed to satisfy the
  requirement. One course from each `Prereq Sequence ID` is required to satisfy
  the prerequisites for the course.

  It's unclear what `Allow concurrent registration` really means---only a few
  courses have it set to `Y`. Some course pairs, such as CSE 12 and 15L, are
  supposedly corequisites according to the course catalog, but they are not
  listed as corequisites in the table.

- **`isis_major_code_list.xlsx - Major Codes.csv`**: Open [isis_major_code_list.xlsx "Major Codes"](https://docs.google.com/spreadsheets/d/1Mgr99R6OFXJuNO_Xx-j49mBgurpwExKL/edit#gid=616727155) and go to File > Download > Comma Separated Values (.csv). This should be the default name it suggests, so you don't have to worry about setting the name.

  The spreadsheet is a modified version of the publicly available [list of ISIS
  major
  codes](https://blink.ucsd.edu/_files/instructors-tab/major-codes/isis_major_code_list.xlsx).

  We use this to add the major name and CIP major code to the uploaded
  curriculum on the [Curricular Analytics
  website](https://curricularanalytics.org/).

### Uploading

To automatically upload CSV files to Curricular Analytics using [`upload.py`](upload.py), you need to create a copy of [`.env.example`](.env.example) and name it `.env`, then fill in `AUTHENTICITY_TOKEN` and `CA_SESSION`.

- To get `CA_SESSION`, open inspect element and head to Application > Cookies > https://curricularanalytics.org. Copy the cookie value for `_curricularanalytics_session`.

  ![`_curricularanalytics_session` cookie](./docs/ca_session.png)
