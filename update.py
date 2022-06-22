if __name__ == "__main__":
    import sys
    from college_names import college_names
    from output import MajorOutput
    from upload import MajorUploader, track_uploaded_curricula

    _, major_code, college_code = sys.argv
    session = MajorUploader()

    with track_uploaded_curricula("./files/uploaded.yml") as curricula:
        plan_id = session.get_degree_plans(curricula[major_code])[
            f"{major_code}/{college_names[college_code]}"
        ]
        session.edit_degree_plan(
            plan_id, MajorOutput(major_code).output_json(college_code)
        )
        print(f"https://curricularanalytics.org/degree_plans/{plan_id}")
