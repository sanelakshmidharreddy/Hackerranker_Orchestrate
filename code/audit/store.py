from collections import defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set

from .models import Observation

class ObservationStore:
    """In-memory indexed store of all observations across SQL, JSON, TXT, LOG, Activity and Multimodal evidence."""

    def __init__(self):
        self._by_resource_id: Dict[str, List[Observation]] = defaultdict(list)
        self._by_identifier: Dict[str, List[Observation]] = defaultdict(list)
        self._by_source_id: Dict[str, List[Observation]] = defaultdict(list)
        self._all_observations: List[Observation] = []

    def add(self, obs: Observation) -> None:
        self._all_observations.append(obs)
        if obs.resource_id:
            self._by_resource_id[obs.resource_id].append(obs)
        for ident in obs.identifiers:
            self._by_identifier[ident].append(obs)
        self._by_source_id[obs.source_id].append(obs)

    def add_many(self, observations: Iterable[Observation]) -> None:
        for obs in observations:
            self.add(obs)

    def finalize(self) -> None:
        """Sort all indexed lists chronologically by observed_at."""
        for r_list in self._by_resource_id.values():
            r_list.sort(key=lambda o: (o.observed_at, o.source_id))
        for i_list in self._by_identifier.values():
            i_list.sort(key=lambda o: (o.observed_at, o.source_id))
        for s_list in self._by_source_id.values():
            s_list.sort(key=lambda o: (o.observed_at, o.source_id))
        self._all_observations.sort(key=lambda o: (o.observed_at, o.source_id))

    def get_for_resource(
        self, resource_id: str, up_to: Optional[datetime] = None
    ) -> List[Observation]:
        obs_list = self._by_resource_id.get(resource_id, [])
        if up_to is not None:
            return [o for o in obs_list if o.observed_at <= up_to]
        return list(obs_list)

    def get_for_identifier(
        self, identifier: str, up_to: Optional[datetime] = None
    ) -> List[Observation]:
        obs_list = self._by_identifier.get(identifier, [])
        if up_to is not None:
            return [o for o in obs_list if o.observed_at <= up_to]
        return list(obs_list)

    def get_for_identifiers(
        self, identifiers: Set[str], up_to: Optional[datetime] = None
    ) -> List[Observation]:
        seen = set()
        result = []
        for ident in identifiers:
            for o in self._by_identifier.get(ident, []):
                if up_to is not None and o.observed_at > up_to:
                    continue
                k = (o.source_id, o.resource_id, o.observed_at, o.raw_ref)
                if k not in seen:
                    seen.add(k)
                    result.append(o)
        result.sort(key=lambda o: (o.observed_at, o.source_id))
        return result

    def get_for_source(
        self, source_id: str, up_to: Optional[datetime] = None
    ) -> List[Observation]:
        obs_list = self._by_source_id.get(source_id, [])
        if up_to is not None:
            return [o for o in obs_list if o.observed_at <= up_to]
        return list(obs_list)

    def get_all_observations(self) -> List[Observation]:
        return list(self._all_observations)
