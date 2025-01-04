from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

EXAMPLE_PRS = [
    {"name": "Implement PDF Support", "url": "https://github.com/cyclotruc/gitingest/pull/80"},
    {"name": "Add swap count", "url": "https://github.com/RodrigoDLPontes/visualization-tool/pull/245"},
    {"name": "Refactor exclusion checks", "url": "https://github.com/apple/foundationdb/pull/11835"}
]
