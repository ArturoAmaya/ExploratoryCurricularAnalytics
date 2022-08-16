module Output

include("Parse.jl")

import CurricularAnalytics: add_requisite!, Course, Curriculum, DegreePlan, isvalid_degree_plan, pre, Requisite, Term
import .Parse: CourseCode, get_plans, get_prereqs

export colleges, output, termname

plans = get_plans()
prereqs = get_prereqs()

const colleges = ["RE", "MU", "TH", "WA", "FI", "SI", "SN"]

const non_course_prereqs = Dict{String,Vector{CourseCode}}(
  "SOCI- UD METHODOLOGY" => [("SOCI", "60")],
  "TDHD XXX" => [("TDTR", "10")],
)

# Mapping academic plan terms to prereq terms (assuming S1 for SU)
const quarter_names = ["FA", "WI", "SP", "S1"]

function termname(start_year::Int, term_idx::Int)
  quarter = quarter_names[mod1(term_idx, 4)]
  quarter * string(if quarter == "FA"
      # Starts at FA21 for 2021 + 0 years
      start_year % 100 + fld(term_idx - 1, 4)
    else
      # Starts at WI22 for 2021 + 0 years
      start_year % 100 + fld(term_idx - 1, 4) + 1
    end, pad=2)
end

function output(year::Int, major::AbstractString)
  academic_plans = plans[year][major]
  degree_plans = Dict{String,DegreePlan}()

  non_courses = Dict(key => Course[] for key in keys(non_course_prereqs))

  for college_code in colleges
    if college_code ∉ keys(academic_plans)
      continue
    end

    # Cache of identifiable courses (and the term index)
    courses = Dict{CourseCode,Tuple{Course,Int}}()

    # This creates `Course`s for non-courses. Note that courses with the same
    # title aren't shared across degree plans. That's too complicated
    terms = [Term([
      begin
        # Repurposing `institution` for whether it's a major or GE and
        # `canonical_name` for the term name
        ca_course = Course(
          course.raw_title,
          course.units,
          prefix=if course.code !== nothing
            course.code[1]
          else
            ""
          end,
          num=if course.code !== nothing
            course.code[2]
          else
            ""
          end,
          institution=if course.for_major
            "DEPARTMENT"
          else
            "COLLEGE"
          end,
          canonical_name=termname(year, i)
        )
        if course.code !== nothing
          courses[course.code] = ca_course, i
        else
          if course.raw_title ∈ keys(non_courses)
            push!(non_courses[course.raw_title], ca_course)
          end
        end
        ca_course
      end
      for course in term
    ]) for (i, term) in enumerate(academic_plans[college_code]) if !isempty(term)]

    # Add prereqs
    for (course_code, (course, i)) in courses
      term = course.canonical_name
      if term ∉ keys(prereqs)
        # Assume the most recent term if the term doesn't have prereqs available
        # (eg FA23)
        term = "WI23"
      end
      if course_code ∈ keys(prereqs[term])
        for requirement in prereqs[term][course_code]
          for option in requirement
            if option ∈ keys(courses) && courses[option][2] < i
              add_requisite!(courses[option][1], course, pre)
              break
            end
          end
        end
      end
    end
    for (key, courses) in non_courses
      for prereq in non_course_prereqs[key]
        if prereq in keys(courses)
          for course in courses
            add_requisite!(courses[prereq], course, pre)
          end
        end
      end
    end

    degree_plans[college_code] = DegreePlan(
      "$major $college_code $year",
      Curriculum(major, Course[]),
      terms,
      Course[]
    )
    # Not helpful because it keeps listing "-Course ELECTIVE is listed multiple
    # times in degree plan"
    # if !isvalid_degree_plan(degree_plans[college_code])
    #   errors = IOBuffer()
    #   isvalid_degree_plan(degree_plans[college_code], errors)
    #   error("$major $college_code $year $(String(take!(errors)))")
    # end
  end

  degree_plans
end

end
