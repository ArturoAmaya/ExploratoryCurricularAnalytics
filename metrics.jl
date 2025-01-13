module Metrics

include("Output.jl")
include("Utils.jl")

import CurricularAnalytics: basic_metrics, Course, course_from_id, Curriculum, extraneous_requisites
import .Output: colleges, output, plans, termname
import .Utils: convert, writerow

open("./files/metrics_fa12.csv", "w") do file
  writerow(file, [
    "Year",
    "Major",
    "College",
    # Views
    "Complexity score",
    "Units #",
    "Units in major #",
    "Units not in major #",
    "Longest path #",
    "Longest path courses",
    "Highest complexity #",
    "Highest complexity name",
    "Highest centrality #",
    "Highest centrality name",
    "Highest term unit load",
    "Highest term unit load name",
    "Lowest term unit load",
    "Lowest term unit load name",
    "# redundant prereqs",
    "Redundant prereqs",
    "% of courses with prerequisites",
    "% of units in major",
    # Flags
    "Under 180 units?",
    "Over 200 units?",
    "Has > 16-unit term?",
    "Has < 12-unit term?",
    "Has > 6 unit difference across colleges?",
  ])

  # idk if Julia supports infinite ranges
  for year in 2015:2050
    if year ∉ keys(plans)
      break
    end
    for major in sort(collect(keys(plans[year])))
      degree_plans = output(year, major)
      plan_units = [plan.credit_hours for plan in values(degree_plans)]

      for college in colleges
        # Ignoring Seventh before 2020 because its plans were scuffed (and it
        # didn't exist)
        if college ∉ keys(degree_plans) || college == "SN" && year < 2020
          continue
        end

        plan = degree_plans[college]
        curriculum = convert(Curriculum, plan)
        try
          basic_metrics(curriculum)
        catch error
          # BoundsError: attempt to access 0-element Vector{Vector{Course}} at
          # index [1] For curricula like AN26 with no prerequisites, presumably
          if !(error isa BoundsError)
            throw(error)
          end
        end

        longest_path = if isempty(curriculum.metrics["longest paths"])
          Course[]
        else
          curriculum.metrics["longest paths"][1]
        end
        major_units = sum(
          course.credit_hours
          for course in curriculum.courses
          if course.institution == "DEPARTMENT";
          init=0
        )
        min_term_units, max_term_units = extrema(term.credit_hours for term in plan.terms)

        redundant_reqs = extraneous_requisites(curriculum)

        writerow(file, String[
          string(year), # Year
          major, # Major
          college, # College
          # Views
          string(curriculum.metrics["complexity"][1]), # Complexity score
          string(plan.credit_hours), # Units #
          string(major_units), # Units in major #
          string(plan.credit_hours - major_units), # Units not in major #
          string(length(longest_path)), # Longest path #
          string(join((course.name for course in longest_path), " → ")), # Longest path courses
          string(curriculum.metrics["max. complexity"]), # Highest complexity #
          curriculum.metrics["max. complexity courses"][1].name, # Highest complexity name
          string(curriculum.metrics["max. centrality"]), # Highest centrality #
          curriculum.metrics["max. centrality courses"][1].name, # Highest centrality name
          string(max_term_units), # Highest term unit load
          termname(year, findfirst(term.credit_hours == max_term_units for term in plan.terms)), # Highest term unit load name
          string(min_term_units), # Lowest term unit load
          termname(year, findfirst(term.credit_hours == min_term_units for term in plan.terms)), # Lowest term unit load name
          string(length(redundant_reqs)), # # redundant prereqs
          join(("$(course_from_id(curriculum, prereq).name) → $(course_from_id(curriculum, course).name)" for (prereq, course) in redundant_reqs), ", "), # Redundant prereqs
          string(count(curriculum.courses) do course
            !isempty(course.requisites)
          end / length(curriculum.courses)), # % of courses with prerequisites
          string(major_units / plan.credit_hours), # % of units in major
          # Flags
          string(plan.credit_hours < 180), # Under 180 units?
          string(plan.credit_hours > 200), # Over 200 units?
          string(any(term.credit_hours > 16 for term in plan.terms)), # Has > 16-unit term?
          string(any(term.credit_hours < 12 for term in plan.terms)), # Has < 12-unit term?
          string(maximum(plan_units) - minimum(plan_units) > 6), # Has > 6 unit difference across colleges?
        ])
      end
    end
  end
end

end
