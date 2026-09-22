# Examples & Walkthroughs

## Example 1: Foundational Topics with Prerequisite Gating

```python
from path_planning_agent import ConceptGraph, TopicNode, PathPlanningAgent, InMemoryProvider

# Setup graph
graph = ConceptGraph()
graph.add_topic(TopicNode(id="arrays", name="Arrays", estimated_duration=30))
graph.add_topic(TopicNode(id="linked_lists", name="Linked Lists", estimated_duration=60))
graph.add_topic(TopicNode(id="recursion", name="Recursion", estimated_duration=60))
graph.add_topic(TopicNode(id="trees", name="Trees", estimated_duration=90))

# Prerequisites
graph.add_prerequisite("linked_lists", "arrays")
graph.add_prerequisite("trees", "linked_lists")
graph.add_prerequisite("trees", "recursion")

provider = InMemoryProvider(graph=graph)

# Case A: Complete beginner (no mastery)
agent = PathPlanningAgent(graph_provider=provider, mastery_provider=provider, mastery_threshold=0.75)
roadmap = agent.generate_roadmap("student_1", time_budget=120)

for item in roadmap.items:
    print(f"{item.topic.name}: {item.status.value} ({item.reason})")

# Output:
# Arrays: SCHEDULED (Foundational topic)
# Recursion: SCHEDULED (Foundational topic)
# Linked Lists: BLOCKED (requires Arrays >= 75%)
# Trees: BLOCKED (requires Linked Lists and Recursion >= 75%)
```

## Example 2: Inspecting Next Topic

```python
next_item = roadmap.next_recommended_topic
print(f"Study Next: {next_item.topic.name}")
print(f"Allocated: {roadmap.allocated_minutes}m / {roadmap.weekly_budget}m")
```
