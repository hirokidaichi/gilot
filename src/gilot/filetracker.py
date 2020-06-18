
from __future__ import annotations

import re
from typing import Dict,List,Tuple,Optional
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__)

OPEN = "{"
CLOSE = "}"
TRANS = "=>"
FRAGMENT = "([^{}=>]*)"
SP = " "
BEGIN = "^"
END = "$"
OR = "|"
TRANSOPS = SP + TRANS + SP
SIMPLE = BEGIN + FRAGMENT + TRANSOPS + FRAGMENT + END
SEPARETE = BEGIN + FRAGMENT + OPEN + FRAGMENT + TRANSOPS + FRAGMENT + CLOSE + FRAGMENT + END

simple = re.compile(SIMPLE)
separete = re.compile(SEPARETE)


def track_name(before:str,after:str,begin:str = "",end:str = "") -> Tuple[str,str]:
    before_name = begin + before + end
    after_name = begin + after + end
    return (before_name,after_name)


def match(str:str) -> Optional[Tuple[str,str]]:
    mo = simple.match(str)
    if mo:
        return track_name(mo.group(1),mo.group(2))
    mo = separete.match(str)
    if mo:
        return track_name(mo.group(2),mo.group(3),mo.group(1),mo.group(4))
    return None


@dataclass
class FileTracker():
    track_map : Dict[str,str]

    def _search_recursive(self, file_name: str) -> str:
        if (file_name not in self.track_map):
            return file_name
        return self._search_recursive(self.track_map[file_name])

    def newest_name(self, file_expression: str) -> str:
        result = match(file_expression)
        name = file_expression if not result else result[1]
        newest_name = self._search_recursive(name)
        logger.debug(f"newestname {newest_name}")
        return newest_name

    @classmethod
    def create(cls, file_expressions: List[str]) -> FileTracker:
        track_map = dict()
        for fe in reversed(file_expressions):
            result = match(fe)
            if result:
                before = result[0]
                after = result[1]
                logger.debug(f"expression: {fe}")
                logger.debug(f"before {before} => after {after}")

                track_map[before] = after
                # A -> B ( A => B)
                # B -> C ( A => B, B => C )
                # C -> A ( [A => B], B => C, C => A ) delete A -> B
                if after in track_map:
                    logger.info(f"delete avoiding cyclic rename:{after}")
                    del track_map[after]

        return cls(track_map=track_map)
