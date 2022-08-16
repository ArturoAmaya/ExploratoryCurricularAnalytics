module Parse

import CurricularAnalytics

export CourseCode, get_prereqs, get_plans

const CourseCode = Tuple{String,String}

function parsefield(field::AbstractString)
  if length(field) > 0 && field[1] == '"'
    field = replace(field[2:end-1], "\"\"" => "\"")
  end
  return strip(field)
end

function parsecsv(io::IO)
  rows = Vector{String}[]
  row_overflow = nothing
  for line in eachline(io, keep=true)
    row = String[]
    in_quotes = false
    if row_overflow !== nothing
      row = row_overflow.row
      in_quotes = true
    else
      row = String[]
      push!(rows, row)
    end
    last_index = 1
    line *= ","
    for i in eachindex(line)
      char = line[i]
      if in_quotes
        if char == '"'
          in_quotes = false
        end
      elseif char == '"'
        in_quotes = true
      elseif char == ','
        prefix = if row_overflow !== nothing
          row_overflow.overflow
        else
          ""
        end
        row_overflow = nothing
        push!(row, parsefield(prefix * line[last_index:prevind(line, i)]))
        last_index = i + 1
      end
    end
    if in_quotes
      prefix = if row_overflow !== nothing
        row_overflow.overflow
      else
        ""
      end
      row_overflow = (row=row, overflow=prefix * line[last_index:end] * "\n")
    end
  end
  rows
end

function get_prereqs()
  # Term => Course => requirements -> alternatives -> requisite
  terms = Dict{String,Dict{CourseCode,Vector{Vector{CourseCode}}}}()

  for (
    term, # Term Code
    _, # Term ID
    _, # Course ID
    sub, # Course Subject Code
    num, # Course Number
    req_seq, # Prereq Sequence ID
    _, # Prereq Course ID
    req_sub, # Prereq Subject Code
    req_num, # Prereq Course Number
    _, # Prereq Minimum Grade Priority
    _, # Prereq Minimum Grade
    _, # Allow concurrent registration (TODO: can I ignore this?)
  ) in open(parsecsv, "./files/prereqs_fa12.csv")[2:end]
    if req_seq == ""
      continue
    end
    courses = get!(terms, term, Dict())
    prereqs = get!(courses, (sub, num), [])
    req_seq = parse(Int, req_seq)
    while req_seq > length(prereqs)
      push!(prereqs, [])
    end
    push!(prereqs[req_seq], (req_sub, req_num))
  end

  # Add prereq overrides
  for term in values(terms)
    term["DOC", "2"] = [[("DOC", "1")]]
  end

  terms
end

const unit_overrides = Dict{CourseCode,Float32}(
  ("MATH", "11") => 5,
  ("CAT", "2") => 6,
  ("CAT", "3") => 6,
  ("PHYS", "1C") => 3,
)

function parse_course_name(name::String)
  name = strip(name, ['^', '*', ' '])
  if name == "UD Domain Elective 1 (if MATH 180A not taken)" || startswith(name, "ADV. CHEM")
    return [(nothing, nothing)]
  end
  name = replace(name, r"DF-?\d - " => "")
  m = match(r"\b([A-Z]{2,4}) *(\d+[A-Z]{0,2})(?: *[&/] *\d?[A-Z]([LX]))?", name)
  if m !== nothing
    subject, number, has_lab = m
    if subject ∉ ["IE", "RR"]
      return if has_lab === nothing
        [((subject, number), if (subject, number) in keys(unit_overrides)
          unit_overrides[subject, number]
        end)]
      else
        units = if has_lab == "L"
          3
        else
          2.5
        end
        [((subject, number), units), ((subject, number * has_lab), 5 - units)]
      end
    end
  end
  [(nothing, nothing)]
end

struct Course
  raw_title::String
  code::Union{CourseCode,Nothing}
  units::Float32
  for_major::Bool
end

function get_plans()
  # Year => Major => College => plan -> term -> course
  years = Dict{Int,Dict{String,Dict{String,Vector{Vector{Course}}}}}()
  for (
    _, # Department
    major, # Major
    college, # College
    course_title, # Course
    units, # Units
    crse_type, # Course Type
    overlaps, # GE/Major Overlap
    plan_year, # Start Year
    year, # Year Taken
    qtr, # Quarter Taken
    _, # Term Taken
  ) in open(parsecsv, "./files/academic_plans_fa12.csv")[2:end]
    majors = get!(years, parse(Int, plan_year), Dict())
    colleges = get!(majors, major, Dict())
    plan = get!(colleges, college, [[] for _ in 1:16])
    # TODO: A lot of plans will have empty terms due to no summer quarter. Will
    # that affect the CA score?
    term = (parse(Int, year) - 1) * 4 + parse(Int, qtr)
    units = parse(Float32, units)
    parsed = parse_course_name(course_title)
    for_major = crse_type == "DEPARTMENT" || overlaps == "Y"
    for (course_code, course_units) in parsed
      course_units = if course_units === nothing
        units
      else
        course_units
      end
      push!(plan[term], Course(course_title, course_code, course_units, for_major))
    end
  end
  years
end

end
