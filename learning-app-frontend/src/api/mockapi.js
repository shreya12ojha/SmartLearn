// Simulates all backend calls. Each function mirrors a real endpoint from
// our API contract — swap the internals for real fetch() calls later.

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// --- Adaptive quiz content, organized by subject → subtopic → difficulty ---
const subjectBanks = {
  dsa: {
    subtopics: [
      {
        id: 'arrays', name: 'Arrays', resource: 'NeetCode 150: Arrays',
        questions: {
          Beginner: [
            { id: 'dsa_arr_b1', text: 'What is the index of the first element in an array?', options: ['1', '0', '-1', 'Depends on language'], correct: '0' },
            { id: 'dsa_arr_b2', text: 'What is the time complexity of accessing an array element by index?', options: ['O(1)', 'O(n)', 'O(log n)', 'O(n^2)'], correct: 'O(1)' },
          ],
          Intermediate: [
            { id: 'dsa_arr_i1', text: 'What is the time complexity of binary search on a sorted array?', options: ['O(n)', 'O(log n)', 'O(n log n)', 'O(1)'], correct: 'O(log n)' },
            { id: 'dsa_arr_i2', text: 'What is the time complexity of inserting an element at the start of an array?', options: ['O(1)', 'O(log n)', 'O(n)', 'O(n^2)'], correct: 'O(n)' },
          ],
          Advanced: [
            { id: 'dsa_arr_a1', text: "What is the time complexity of Kadane's Algorithm for max subarray sum?", options: ['O(n^2)', 'O(n log n)', 'O(n)', 'O(2^n)'], correct: 'O(n)' },
            { id: 'dsa_arr_a2', text: 'Which technique efficiently solves the "3Sum" problem?', options: ['Brute force', 'Two pointers after sorting', 'Recursion only', 'Hashing without sorting'], correct: 'Two pointers after sorting' },
          ],
        },
      },
      {
        id: 'linked_lists', name: 'Linked Lists', resource: 'GFG: Linked List Practice',
        questions: {
          Beginner: [{ id: 'dsa_ll_b1', text: 'What does each node in a singly linked list store?', options: ['Only data', 'Data + pointer to next node', 'Data + pointer to previous node', 'Only pointers'], correct: 'Data + pointer to next node' }],
          Intermediate: [{ id: 'dsa_ll_i1', text: 'What is the time complexity of reversing a singly linked list?', options: ['O(1)', 'O(log n)', 'O(n)', 'O(n^2)'], correct: 'O(n)' }],
          Advanced: [{ id: 'dsa_ll_a1', text: 'Which algorithm detects a cycle in a linked list in O(1) space?', options: ['Merge sort', "Floyd's cycle detection", 'Binary search', 'DFS'], correct: "Floyd's cycle detection" }],
        },
      },
      {
        id: 'trees', name: 'Trees & BSTs', resource: "Striver's SDE Sheet: Trees",
        questions: {
          Beginner: [{ id: 'dsa_tr_b1', text: 'In a Binary Search Tree, where are smaller values stored relative to a node?', options: ['Right subtree', 'Left subtree', 'Root only', 'Anywhere'], correct: 'Left subtree' }],
          Intermediate: [{ id: 'dsa_tr_i1', text: 'Which traversal of a BST gives sorted output?', options: ['Pre-order', 'Post-order', 'In-order', 'Level-order'], correct: 'In-order' }],
          Advanced: [{ id: 'dsa_tr_a1', text: 'What is the time complexity of finding the LCA in a balanced BST?', options: ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], correct: 'O(log n)' }],
        },
      },
    ],
  },
  cn: {
    subtopics: [
      { id: 'osi_model', name: 'OSI Model', resource: 'GFG: OSI Model Basics', questions: {
        Beginner: [{ id: 'cn_osi_b1', text: 'How many layers does the OSI model have?', options: ['5', '6', '7', '4'], correct: '7' }],
        Intermediate: [{ id: 'cn_osi_i1', text: 'Which layer is responsible for routing?', options: ['Data Link', 'Network', 'Transport', 'Session'], correct: 'Network' }],
        Advanced: [{ id: 'cn_osi_a1', text: 'Which layer handles end-to-end congestion control?', options: ['Network', 'Transport', 'Session', 'Application'], correct: 'Transport' }],
      }},
      { id: 'tcp_udp', name: 'TCP vs UDP', resource: 'GFG: TCP vs UDP', questions: {
        Beginner: [{ id: 'cn_tcp_b1', text: 'Which protocol is connection-oriented?', options: ['UDP', 'TCP', 'IP', 'ARP'], correct: 'TCP' }],
        Intermediate: [{ id: 'cn_tcp_i1', text: 'What mechanism does TCP use to ensure reliable delivery?', options: ['Best-effort', 'Acknowledgements & retransmission', 'No guarantee', 'Broadcasting'], correct: 'Acknowledgements & retransmission' }],
        Advanced: [{ id: 'cn_tcp_a1', text: "What is TCP's three-way handshake sequence?", options: ['SYN, SYN-ACK, ACK', 'ACK, SYN, FIN', 'SYN, FIN, ACK', 'ACK only'], correct: 'SYN, SYN-ACK, ACK' }],
      }},
    ],
  },
  os: {
    subtopics: [
      { id: 'processes', name: 'Processes & Threads', resource: 'GFG: Process vs Thread', questions: {
        Beginner: [{ id: 'os_proc_b1', text: 'What is a process?', options: ['A program in execution', 'A file on disk', 'A hardware device', 'A network packet'], correct: 'A program in execution' }],
        Intermediate: [{ id: 'os_proc_i1', text: 'What is the main advantage of threads over processes?', options: ['More memory usage', 'Lighter weight, shared memory', 'Slower context switch', 'No shared resources'], correct: 'Lighter weight, shared memory' }],
        Advanced: [{ id: 'os_proc_a1', text: 'Which condition is necessary for deadlock?', options: ['Mutual exclusion, hold & wait, no preemption, circular wait', 'Only mutual exclusion', 'Only circular wait', 'None needed'], correct: 'Mutual exclusion, hold & wait, no preemption, circular wait' }],
      }},
    ],
  },
  oops: {
    subtopics: [
      { id: 'pillars', name: 'OOP Pillars', resource: 'GFG: 4 Pillars of OOP', questions: {
        Beginner: [{ id: 'oop_p_b1', text: 'Which of these is NOT a pillar of OOP?', options: ['Encapsulation', 'Inheritance', 'Compilation', 'Polymorphism'], correct: 'Compilation' }],
        Intermediate: [{ id: 'oop_p_i1', text: 'What does polymorphism allow?', options: ['One interface, multiple implementations', 'Hiding data only', 'Only single inheritance', 'Faster compilation'], correct: 'One interface, multiple implementations' }],
        Advanced: [{ id: 'oop_p_a1', text: 'What is the difference between compile-time and runtime polymorphism?', options: ['No difference', 'Method overloading vs overriding', 'Both are the same as inheritance', 'Only applies to interfaces'], correct: 'Method overloading vs overriding' }],
      }},
    ],
  },
  dbms: {
    subtopics: [
      { id: 'normalization', name: 'Normalization', resource: 'GFG: Normal Forms', questions: {
        Beginner: [{ id: 'db_norm_b1', text: 'What is the purpose of normalization?', options: ['Increase redundancy', 'Reduce redundancy & improve integrity', 'Slow down queries', 'Delete data'], correct: 'Reduce redundancy & improve integrity' }],
        Intermediate: [{ id: 'db_norm_i1', text: 'What does 3NF eliminate that 2NF does not?', options: ['Partial dependency', 'Transitive dependency', 'Multivalued dependency', 'Nothing new'], correct: 'Transitive dependency' }],
        Advanced: [{ id: 'db_norm_a1', text: 'BCNF is a stricter version of which normal form?', options: ['1NF', '2NF', '3NF', '4NF'], correct: '3NF' }],
      }},
    ],
  },
}

const subjectNames = {
  dsa: 'Data Structures & Algorithms',
  cn: 'Computer Networks',
  os: 'Operating Systems',
  oops: 'OOPs',
  dbms: 'DBMS',
}

// --- Matches: POST /api/auth/signup ---
export async function signup({ name, email, password }) {
  await delay(400)
  return { token: 'mock-token-123', user_id: 'u1' }
}

// --- Matches: POST /api/auth/login ---
export async function login({ email, password }) {
  await delay(400)
  return { token: 'mock-token-123', user_id: 'u1' }
}

// --- Adaptive quiz bank for a subject, keyed by subtopic → difficulty ---
export async function fetchAdaptiveQuizBank(subject) {
  await delay(300)
  const bank = subjectBanks[subject] || subjectBanks.dsa
  return { subtopics: bank.subtopics, subjectName: subjectNames[subject] || subject }
}

// --- Matches: GET /api/roadmap/:user_id ---
const topicMeta = [
  { id: 'arrays', name: 'Arrays & Strings', resource: 'NeetCode 150: Arrays' },
  { id: 'linked_lists', name: 'Linked Lists', resource: 'GFG: Linked List Practice' },
  { id: 'trees', name: 'Trees & BSTs', resource: "Striver's SDE Sheet: Trees" },
  { id: 'osi_model', name: 'OSI Model', resource: 'GFG: OSI Model Basics' },
  { id: 'tcp_udp', name: 'TCP vs UDP', resource: 'GFG: TCP vs UDP' },
  { id: 'processes', name: 'Processes & Threads', resource: 'GFG: Process vs Thread' },
  { id: 'pillars', name: 'OOP Pillars', resource: 'GFG: 4 Pillars of OOP' },
  { id: 'normalization', name: 'Normalization', resource: 'GFG: Normal Forms' },
]

export async function fetchRoadmap(mastery) {
  await delay(300)
  return {
    topics: topicMeta
      .filter((t) => mastery[t.id] !== undefined)
      .map((t) => ({ ...t, mastery: mastery[t.id] ?? 0 })),
  }
}

// --- Estimates days-to-complete based on remaining subtopics + daily hours ---
export async function fetchPacingEstimate(subject, mastery, hoursPerDay) {
  await delay(200)
  const bank = subjectBanks[subject] || subjectBanks.dsa
  const totalSubtopics = bank.subtopics.length
  const completedSubtopics = bank.subtopics.filter(
    (s) => (mastery[s.id] || 0) >= 0.6
  ).length
  const remaining = totalSubtopics - completedSubtopics
  const HOURS_PER_SUBTOPIC = 2 // rough assumption — Path Planning Agent will refine this later
  const estimatedDays = remaining === 0
    ? 0
    : Math.ceil((remaining * HOURS_PER_SUBTOPIC) / (hoursPerDay || 1))

  return { totalSubtopics, completedSubtopics, remaining, estimatedDays }
}

// --- Matches: POST /api/checkpoint ---
// Given a topic (subtopic) id, finds which subject it belongs to and its
// position within that subject's subtopic list. The frontend uses this to
// jump the adaptive quiz engine directly to that subtopic for a retest,
// instead of restarting the whole subject from the beginning.
export async function checkpointRetest(topicId) {
  await delay(200)
  for (const [subjectId, bank] of Object.entries(subjectBanks)) {
    const subtopicIndex = bank.subtopics.findIndex((s) => s.id === topicId)
    if (subtopicIndex !== -1) {
      return { subject: subjectId, subtopicIndex, topicId }
    }
  }
  return null // topic not found in any subject bank — nothing to retest
}