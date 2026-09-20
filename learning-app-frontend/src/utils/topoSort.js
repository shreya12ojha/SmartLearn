export function topoSortTopics(topics, prerequisites) {
  const ids = topics.map((t) => t.id)
  const idSet = new Set(ids)
  const inDegree = {}
  const adj = {}
  ids.forEach((id) => {
    inDegree[id] = 0
    adj[id] = []
  })
  prerequisites.forEach((p) => {
    if (idSet.has(p.topic_id) && idSet.has(p.prerequisite_topic_id)) {
      adj[p.prerequisite_topic_id].push(p.topic_id)
      inDegree[p.topic_id] += 1
    }
  })
  const queue = ids.filter((id) => inDegree[id] === 0)
  const order = []
  while (queue.length) {
    const id = queue.shift()
    order.push(id)
    adj[id].forEach((next) => {
      inDegree[next] -= 1
      if (inDegree[next] === 0) queue.push(next)
    })
  }
  ids.forEach((id) => {
    if (!order.includes(id)) order.push(id)
  })
  return order.map((id) => topics.find((t) => t.id === id))
}