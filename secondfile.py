import parse

for major in parse.majors:
    #print(major.department + major.major)
    temp_curr_RE = major.curriculum("RE")
    temp_curr_MU = major.curriculum("MU")
    temp_curr_FI = major.curriculum("FI")
    temp_curr_SI = major.curriculum("SI")
    temp_curr_SN = major.curriculum("SN")
    temp_curr_TH = major.curriculum("TH")
    temp_curr_WA = major.curriculum("WA")

    if (temp_curr)
