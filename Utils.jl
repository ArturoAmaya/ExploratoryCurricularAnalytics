module Utils

import CurricularAnalytics: Curriculum, DegreePlan, isvalid_curriculum

export convert, writerow

function convert(::Type{Curriculum}, plan::DegreePlan)
  c = Curriculum(plan.name, [course for term in plan.terms for course in term.courses])
  if !isvalid_curriculum(c)
    error("$(plan.name) is not a valid curriculum")
  end
  c
end

function writerow(io::IO, row::AbstractVector{String})
  join(io, [
      if any([',', '"', '\r', '\n'] .∈ field)
        "\"$(replace(field, "\"" => "\"\""))\""
      else
        field
      end for field in row
    ], ",")
  write(io, "\n")
  flush(io)
end

end
