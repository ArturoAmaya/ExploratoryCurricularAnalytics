# Curricular Analytics API documentation

## Authentication

The `_curricularanalytics_session` cookie is needed for all requests. You can obtain yours in inspect element by going to Application > Cookies > https://curricularanalytics.org.

If the session cookie is invalid, Curricular Analytics will either respond with an HTTP 401 (Unauthorized) status code or, for forms, redirect you to https://curricularanalytics.org/users/sign_in.

Generally, only requests that modify something, i.e. POST and PATCH requests, not GET requests, also require a CSRF/authentication token (Curricular Analytics uses both terms). The website generates a new one every time, but it doesn't store these tokens; instead, it does some hash magic between your session and the CSRF token to see if it is valid. Therefore, you can get the CSRF token once, and it'll work for all requests.

To get a CSRF token, most pages should have `<meta name="csrf-token" content="[...]" />` in the HTML. Some forms will also have a `<input type="hidden" name="authenticity_token" value="[...]" />`.

If the CSRF token is invalid, Curricular Analytics will respond with an HTTP 422 (Unprocessable Entity) status code.

## Uploading new curricula and degree plans

```http
POST /curriculums
POST /degree_plans
```

Curricula and degree plans can be uploaded either as JSON (produced by the GUI editor; see [editing curricula/degree plans](#editing-an-existing-curriculum-or-degree-plan) for the format) or a [CSV file](https://curricularanalytics.org/files). Uploading by JSON tends to be slower than uploading a CSV file, it seems.

The request body should be a `Content-Type: multipart/form-data` because it includes a file. The request body has the following fields:

- `authenticity_token`: [the CSRF token](#authentication)
- `entry_method`: either `gui` for JSON or `csv_file` for CSV
- `curriculum[curriculum_file]`: if uploading a CSV, the CSV file contents. Curricular Analytics also uses the `filename` of the file.
- `curriculum_json`: if uploading by JSON, the JSON string

For a new curriculum, the request body has the following additional fields:

- `curriculum[name]`: the curriculum name
- `curriculum[organization_id]`: the ID of the organization to add the curriculum to
- `curriculum[catalog_year]`: the catalog year of the curriculum
- `curriculum[cip]`: the CIP major code of the curriculum. Note that you can leave this blank, and Curricular Analytics will automatically fill this in from the CSV file if you upload a CSV file with the CIP field in the header filled in.

For a new degree plan, the request body has the following additional fields:

- `degree_plan[name]`: the degree plan name
- `degree_plan[curriculum_id]`: the ID of the curriculum that the degree plan is part of

Note that on submission, the form redirects you to the page with all of the curricula or degree plans, respectively, which doesn't contain any useful information about the curriculum or degree plan you just created. You can [list the user's curricula](#list-users-curricula) to get the most recently created curriculum.

## List user's curricula

```http
GET /curriculums
```

The `Accept` header must include `application/json`. Otherwise, you will get the [Your Curricula page](https://curricularanalytics.org/curriculums) HTML.

URL parameters:

- `order[0][column]`: the index of the column to sort by

  The columns' indices are as shown on the [Your Curricula page](https://curricularanalytics.org/curriculums):

  0. Name
  1. Organization
  2. CIP code
  3. Catalog year
  4. Date created

  For example, using `4` will sort by creation date.

  Defaults to 0 (name).

- `order[0][dir]`: the direction of the sort, either `asc` for ascending or `desc` for descending. Required.
- `start`: the index of the first result to include, for pagination. Defaults to 0.
- `length`: the number of results to return. Defaults to 10.
- `search[value]`: the search query used to filter the curricula. Leave blank if you're not searching by any query. Required.
- `include_public`: either `true` or `false`, whether to include all public curricula on the website in your results. Defaults to false.

If your `Accept` header is set correctly, it will return JSON of the following format:

```ts
type Response = {
  data: [
    nameHTML: string,
    organizationHTML: string,
    cipCode: string,
    year: number,
    dateCreated: string,
    buttonsHTML: string
  ][]
}
```

`nameHTML`, `organizationHTML`, and `buttonsHTML` contain an HTML string from which you can get the curriculum ID and name in `nameHTML`, organization ID and name in `organizationHTML`, and the curriculum ID and a download link for the uploaded CSV file, if it exists, in `buttonsHTML`.

This is what one such tuple looks like:

```json
[
  "<a href=\"/curriculums/19757\">DS25-Data Science</a>",
  "<a href=\"/organizations/19409\">seyen@ucsd.edu</a>",
  "11.0103",
  2021,
  "2022-06-21 00:38:21 UTC",
  "<a class=\"btn btn-secondary btn-sm\" href=\"/curriculums/19757/edit\">Edit</a> <a data-confirm=\"Are you sure?\" class=\"btn btn-danger btn-sm\" rel=\"nofollow\" data-method=\"delete\" href=\"/curriculums/19757\">Destroy</a> <div class='dropdown'>\n<button aria-expanded='false' aria-haspopup='true' class='btn btn-primary btn-sm dropdown-toggle' data-toggle='dropdown' id='dropdownMenuButton' type='button'>\nDownload\n</button>\n<div aria-labelledby='dropdownMenuButton' class='dropdown-menu'>\n<a class='dropdown-item' href='/rails/active_storage/blobs/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBblJNIiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--4a247724f726e0f8e00248bb81b49bf32c2cf7e9/SY-Curriculum%20Plan-DS25.csv?disposition=attachment'>Original File</a>\n<a data-turbolinks=\"false\" class=\"dropdown-item\" data-method=\"get\" href=\"/curriculums/metrics_csv/19757?include_metrics=true\">File w/ Metrics</a>\n</div>\n</div>\n"
]
```

## Editing an existing curriculum or degree plan

```http
PATCH /curriculums/viz_update/<curriculum id>
PATCH /degree_plans/viz_update/<degree plan id>
```

The `X-CSRF-Token` header must be set to [your CSRF token](#authentication).

The request body should be a `Content-Type: application/json` of the following format:

```ts
type CurriculumRequest = {
  curriculum: Curriculum
}

type DegreePlanRequest = {
  curriculum: Curriculum
  degree_plan: {
    /** The ID of the degree plan to edit. */
    id: number
  }
}
```

where

```ts
type Curriculum = {
  curriculum_terms: Term[]
}

/** A quarter. */
type Term = {
  /** Uses its own ID namespace separate from `Item`s. */
  id: number
  curriculum_items: Item[]
}

/** A course. */
type Item = {
  name: string
  id: number
  /** Defaults to 0, which probably isn't what you want. */
  credits?: number
  curriculum_requisites: Requisite[]
}

type Requisite = {
  /** An `Item` ID. */
  source_id: number
  /** An `Item` ID. */
  target_id: number
  type: 'prereq' | 'coreq' | 'strict-coreq'
}
```

Here is an example degree plan JSON (`DegreePlanRequest`):

```json
{
  "curriculum": {
    "curriculum_terms": [
      {
        "id": 1,
        "curriculum_items": [
          {
            "name": "LANGUAGE 1",
            "id": 14,
            "credits": 5,
            "curriculum_requisites": []
          },
          {
            "name": "CHEMISTRY GE",
            "id": 15,
            "credits": 4,
            "curriculum_requisites": []
          }
        ]
      },
      {
        "id": 2,
        "curriculum_items": [
          {
            "name": "MATH 10A",
            "id": 1,
            "credits": 0,
            "curriculum_requisites": []
          },
          {
            "name": "DEI",
            "id": 16,
            "credits": 4,
            "curriculum_requisites": [
              {
                "source_id": 15,
                "target_id": 16,
                "type": "coreq"
              },
              {
                "source_id": 1,
                "target_id": 16,
                "type": "strict-coreq"
              },
              {
                "source_id": 14,
                "target_id": 16,
                "type": "prereq"
              }
            ]
          }
        ]
      }
    ]
  },
  "degree_plan": { "id": 11293 }
}
```

## Destroying a curriculum or degree plan

```http
POST /curriculums/<curriculum id>
POST /degree_plans/<degree plan id>
```

Deleting curricula and degree plan posts to a form, so the request body is `Content-Type: application/x-www-form-urlencoded` with the following fields:

- `authenticity_token`: [the CSRF token](#authentication)
- `_method`: `delete`
