
from . import ManagerAgent, ReviewAgent, CleanAgent


def to_agent(raw):
    return {
        "manager": ManagerAgent,
        "reviewer": ReviewAgent,
        "cleaner": CleanAgent
    }[raw['name']](**{key: raw[key] for key in raw if key != "name"})
