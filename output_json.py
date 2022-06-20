from typing import List, Literal, TypedDict


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
