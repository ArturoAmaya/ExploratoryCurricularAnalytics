from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


class Requisite(TypedDict):
    source_id: int
    target_id: int
    type: Literal["prereq", "coreq", "strict-coreq"]


class Item(TypedDict):
    name: str
    id: int
    credits: float
    curriculum_requisites: List[Requisite]


class Term(TypedDict):
    id: int
    curriculum_items: List[Item]


class Curriculum(TypedDict):
    curriculum_terms: List[Term]


class CurriculumJson(TypedDict):
    curriculum: Curriculum


class DegreePlan(TypedDict):
    id: int


class DegreePlanJson(TypedDict):
    curriculum: Curriculum
    degree_plan: DegreePlan


class Course(TypedDict):
    id: int
    name: str
    credits: float
    requisites: List[Requisite]
    nameCanonical: Optional[str]
    nameSub: Optional[str]
    annotation: Optional[str]


class CurriculumHash(TypedDict):
    courses: List[Course]
    name: str


class TermHash(TypedDict):
    id: int
    name: str
    items: List[Course]


class DegreePlanHash(TypedDict):
    terms: List[Term]


def object_hook(
    obj: Dict[str, Any]
) -> Union[Requisite, Course, TermHash, CurriculumHash, DegreePlanHash]:
    if "source_id" in obj:
        return Requisite(**obj)
    if "nameCanonical" in obj:
        return Course(**obj)
    if "items" in obj:
        return TermHash(**obj)
    if "courses" in obj:
        return CurriculumHash(**obj)
    if "terms" in obj:
        return DegreePlanHash(**obj)
    raise TypeError(f"Unexpected object {obj}.")
