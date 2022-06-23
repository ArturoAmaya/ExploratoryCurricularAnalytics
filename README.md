## Setup

[`parse.py`](parse.py) expects certain files in the `files/` directory. Download them from the shared Google Drive folder.

- [`academic_plans.csv`](https://drive.google.com/file/d/1vYF4aDBjLrK7pXOkdCPMYwl7TPuWCEVe/view?usp=sharing)

- [`prereqs.csv`](https://drive.google.com/file/d/10KUDrht-0gGPSqwEOQFz10svPoDXq4Wh/view?usp=sharing)

- `isis_major_code_list.xlsx - Major Codes.csv`: Open [isis_major_code_list.xlsx "Major Codes"](https://docs.google.com/spreadsheets/d/1Mgr99R6OFXJuNO_Xx-j49mBgurpwExKL/edit#gid=616727155) and go to File > Download > Comma Separated Values (.csv). This should be the default name it suggests, so you don't have to worry about setting the name.

### Uploading

To automatically upload CSV files to Curricular Analytics using [`upload.py`](upload.py), you need to create a copy of [`.env.example`](.env.example) and name it `.env`, then fill in `AUTHENTICITY_TOKEN` and `CA_SESSION`.

- To get `CA_SESSION`, open inspect element and head to Application > Cookies > https://curricularanalytics.org. Copy the cookie value for `_curricularanalytics_session`.

  ![`_curricularanalytics_session` cookie](./docs/ca_session.png)
