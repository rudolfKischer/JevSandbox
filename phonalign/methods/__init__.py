from . import p_longest, q_pool, r_route, u_em

MODULES = (p_longest, q_pool, r_route, u_em)
REGISTRY = {module.NAME: module for module in MODULES}
