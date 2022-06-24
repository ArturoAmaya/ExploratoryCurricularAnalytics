from typing import List, Literal, Optional, TypedDict


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
    terms: List[TermHash]
