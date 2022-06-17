import output


for college in output.college_names:
    for major in output.major_plans:
        if major != "PS33" and major != "UN27" and major != "UNHA" and major != "UNPS" and major != "UNSS":
            output.to_file(
                f"files/curricula/{major}/{major}_{college}.csv", output.output(major, college))
