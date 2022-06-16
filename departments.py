"""
Loads department codes and names from a JSON file saved from plans.ucsd.edu:
https://plans.ucsd.edu/controller.php?action=LoadSearchControls

Exports:
    `departments`, a dictionary mapping from department codes to their names.
"""

import json
from typing import Dict

__all__ = ["departments"]


departments: Dict[str, str] = {}
with open("./files/LoadSearchControls.json") as controls:
    for department in json.load(controls)["departments"]:
        departments[department["code"]] = department["name"]
