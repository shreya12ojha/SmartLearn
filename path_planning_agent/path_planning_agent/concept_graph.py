from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from path_planning_agent.models import TopicNode


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the concept graph."""
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        super().__init__(f"Cycle detected in concept graph: {' -> '.join(cycle_path)}")


class ConceptGraph:
    """
    Directed Acyclic Graph (DAG) representing topics and their prerequisite relationships.
    Edges are directed from Prerequisite -> Dependent (Topic).
    """

    def __init__(self):
        self._nodes: Dict[str, TopicNode] = {}
        # adj[u] = list of v where u is prerequisite of v (u -> v)
        self._adj: Dict[str, List[str]] = defaultdict(list)
        # prereqs[v] = list of u where u is prerequisite of v
        self._prereqs: Dict[str, List[str]] = defaultdict(list)

    def add_topic(self, topic: TopicNode) -> None:
        """Add a topic node to the graph."""
        self._nodes[str(topic.id)] = topic
        if str(topic.id) not in self._adj:
            self._adj[str(topic.id)] = []
        if str(topic.id) not in self._prereqs:
            self._prereqs[str(topic.id)] = []

    def add_prerequisite(self, topic_id: str, prerequisite_topic_id: str) -> None:
        """
        Add a prerequisite relationship.
        prerequisite_topic_id must be learned before topic_id.
        Edge: prerequisite_topic_id -> topic_id.
        """
        tid = str(topic_id)
        pid = str(prerequisite_topic_id)

        if tid not in self._nodes:
            raise KeyError(f"Topic {tid} not found in graph")
        if pid not in self._nodes:
            raise KeyError(f"Prerequisite topic {pid} not found in graph")

        if tid not in self._adj[pid]:
            self._adj[pid].append(tid)
        if pid not in self._prereqs[tid]:
            self._prereqs[tid].append(pid)

    def get_topic(self, topic_id: str) -> Optional[TopicNode]:
        return self._nodes.get(str(topic_id))

    def get_all_topics(self) -> List[TopicNode]:
        return list(self._nodes.values())

    def get_immediate_prerequisites(self, topic_id: str) -> List[str]:
        """Return list of topic IDs that are direct prerequisites of topic_id."""
        return list(self._prereqs.get(str(topic_id), []))

    def get_immediate_dependents(self, topic_id: str) -> List[str]:
        """Return list of topic IDs that directly depend on topic_id."""
        return list(self._adj.get(str(topic_id), []))

    def get_all_prerequisites(self, topic_id: str) -> Set[str]:
        """Return all transitive prerequisites (ancestors) of topic_id."""
        tid = str(topic_id)
        visited = set()
        queue = deque(self.get_immediate_prerequisites(tid))
        while queue:
            curr = queue.popleft()
            if curr not in visited:
                visited.add(curr)
                queue.extend(self.get_immediate_prerequisites(curr))
        return visited

    def get_all_dependents(self, topic_id: str) -> Set[str]:
        """Return all transitive dependents (descendants) of topic_id."""
        tid = str(topic_id)
        visited = set()
        queue = deque(self.get_immediate_dependents(tid))
        while queue:
            curr = queue.popleft()
            if curr not in visited:
                visited.add(curr)
                queue.extend(self.get_immediate_dependents(curr))
        return visited

    def find_cycles(self) -> List[List[str]]:
        """
        Detect and return cycles in the graph using DFS.
        Returns a list of cycle paths (e.g. [['A', 'B', 'C', 'A']]).
        """
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []
        path: List[str] = []

        for node_id in self._nodes:
            visited[node_id] = 0

        def dfs(u: str):
            visited[u] = 1
            path.append(u)

            for v in self._adj.get(u, []):
                if visited.get(v, 0) == 1:
                    # Found a back-edge / cycle
                    cycle_start = path.index(v)
                    cycles.append(path[cycle_start:] + [v])
                elif visited.get(v, 0) == 0:
                    dfs(v)

            path.pop()
            visited[u] = 2

        for node_id in self._nodes:
            if visited[node_id] == 0:
                dfs(node_id)

        return cycles

    def has_cycle(self) -> bool:
        return len(self.find_cycles()) > 0

    def topological_sort(self) -> List[TopicNode]:
        """
        Perform topological sorting using Kahn's algorithm.
        Raises CycleDetectedError if a cycle is present.
        """
        in_degree: Dict[str, int] = {nid: len(self._prereqs[nid]) for nid in self._nodes}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        ordered_ids: List[str] = []

        while queue:
            u = queue.popleft()
            ordered_ids.append(u)

            for v in self._adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(ordered_ids) < len(self._nodes):
            cycles = self.find_cycles()
            first_cycle = cycles[0] if cycles else ["unknown cycle"]
            raise CycleDetectedError(first_cycle)

        return [self._nodes[nid] for nid in ordered_ids]

    def is_unlocked(self, topic_id: str, mastery_dict: Dict[str, float], threshold: float = 0.75) -> bool:
        """
        A topic is unlocked if ALL its immediate prerequisites meet or exceed the mastery threshold.
        Topics with no prerequisites are always unlocked.
        """
        tid = str(topic_id)
        prereqs = self.get_immediate_prerequisites(tid)
        for pid in prereqs:
            score = mastery_dict.get(pid, 0.0)
            if score < threshold:
                return False
        return True

    def get_blocking_prerequisites(
        self, topic_id: str, mastery_dict: Dict[str, float], threshold: float = 0.75
    ) -> List[Tuple[str, str, float]]:
        """
        Returns list of tuples (prereq_id, prereq_name, current_score) for prerequisites
        that are below the threshold and thus blocking topic_id.
        """
        tid = str(topic_id)
        prereqs = self.get_immediate_prerequisites(tid)
        blocking = []
        for pid in prereqs:
            score = mastery_dict.get(pid, 0.0)
            if score < threshold:
                p_node = self.get_topic(pid)
                p_name = p_node.name if p_node else pid
                blocking.append((pid, p_name, score))
        return blocking
