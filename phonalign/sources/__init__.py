from . import m2m_source, nettalk_source, ours, phonetisaurus, production

REGISTRY = {module.NAME: module for module in (ours, ours.FREE, production, phonetisaurus, m2m_source, nettalk_source)}
