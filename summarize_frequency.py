"""
python3 summarize_frequency.py './files/21-22 Enrollment_DFW CJ.xlsx.csv' './files/Waitlist by Course for CJ.xlsx.csv' > files/protected/summarize_frequency.json
"""


import csv
import json
import sys
from typing import Dict, Set

from parse_defs import TermCode


def main():
    if len(sys.argv) < 2:
        print("python3 summarize_frequency.py <paths...>")
        exit(1)

    course_offerings: Dict[str, Set[TermCode]] = {}
    all_terms: Set[TermCode] = set()

    for path in sys.argv[1:]:
        with open(path) as file:
            reader = csv.reader(file)
            # Skip header
            next(reader)
            next(reader)
            course_code = ""
            for course, _, term, *_ in reader:
                if not term:
                    continue
                course_code = course or course_code
                if not course_code:
                    continue
                if course_code not in course_offerings:
                    course_offerings[course_code] = set()
                if term == "Total":
                    continue
                term = TermCode(term)
                course_offerings[course_code].add(term)
                all_terms.add(term)

    # Sort by course code
    courses = dict(
        (course_code, sorted(terms))
        for course_code, terms in sorted(
            course_offerings.items(), key=lambda item: item[0]
        )
    )

    json.dump({**courses, "total terms": sorted(all_terms)}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
