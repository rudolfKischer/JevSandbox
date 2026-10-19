from ..models import Unit
from ..pool import candidate_pool
from ..result import Result

NAME = "p"
LABEL = "P: longest catalog units, no Jev"


def run(entry, call):
    pool = candidate_pool(entry)
    if not pool:
        return Result([Unit(entry["word"], tuple(entry["pron"].split()))], 0.0, None, [], {"no_tiling": True})
    ranked = sorted(pool, key=lambda units: (len(units), -max(len(u.spelling) for u in units)))
    return Result(ranked[0], None, None, [], {"candidates": len(pool)})
