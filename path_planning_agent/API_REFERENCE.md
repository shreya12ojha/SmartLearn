# API Reference

## Classes

### `TopicNode`
```python
TopicNode(
    id: str,
    name: str,
    domain: str = "DSA",
    difficulty: str = "Beginner",
    estimated_duration: Optional[int] = None,
    metadata: Dict[str, Any] = None
)
```
- `get_duration() -> int`: Returns explicit duration or default based on difficulty (Beginner: 30m, Intermediate: 60m, Advanced: 90m).

### `ConceptGraph`
```python
ConceptGraph()
```
- `add_topic(topic: TopicNode) -> None`
- `add_prerequisite(topic_id: str, prerequisite_topic_id: str) -> None`
- `topological_sort() -> List[TopicNode]` (Kahn's algorithm, raises `CycleDetectedError`)
- `has_cycle() -> bool`
- `find_cycles() -> List[List[str]]`
- `get_immediate_prerequisites(topic_id: str) -> List[str]`
- `get_all_prerequisites(topic_id: str) -> Set[str]`
- `get_immediate_dependents(topic_id: str) -> List[str]`
- `get_all_dependents(topic_id: str) -> Set[str]`
- `is_unlocked(topic_id: str, mastery_dict: Dict[str, float], threshold: float = 0.75) -> bool`
- `get_blocking_prerequisites(topic_id: str, mastery_dict: Dict[str, float], threshold: float = 0.75) -> List[Tuple[str, str, float]]`

### `PathPlanningAgent`
```python
PathPlanningAgent(
    graph_provider: Optional[ConceptGraphProvider] = None,
    mastery_provider: Optional[MasteryProvider] = None,
    context_provider: Optional[StudentContextProvider] = None,
    mastery_threshold: float = 0.75
)
```
- `generate_roadmap(user_id: Union[str, int], ...) -> RoadmapResult`
- `get_next_topic(user_id: Union[str, int], ...) -> Optional[RoadmapItem]`
- `classify_mastery_tier(score: float, is_assessed: bool) -> str`

### `RoadmapResult`
- `user_id: str`
- `weekly_budget: int`
- `allocated_minutes: int`
- `remaining_budget: int`
- `items: List[RoadmapItem]`
- `next_recommended_topic: Optional[RoadmapItem]`
- `to_dict() -> Dict[str, Any]`
- Properties: `scheduled_items`, `mastered_items`, `blocked_items`, `deferred_items`.
