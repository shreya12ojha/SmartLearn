"""
Idempotent Seeder for SmartLearn Learning Resources.
Seeds curated educational resources across 4 formats (video, text, practice, interactive)
for all 11 DSA topics in the question bank.
"""

from app.database import SessionLocal
from app.models import LearningResource, Topic

RESOURCE_DEFINITIONS = [
    # 1. Loops
    {
        "topic": "Loops",
        "resources": [
            {
                "title": "Python Loops & Iteration Deep Dive",
                "url": "https://www.youtube.com/watch?v=6iF8Xb7Z3wQ",
                "format": "video",
                "estimated_time": 25,
                "difficulty": "easy",
            },
            {
                "title": "Understanding For & While Loops in Algorithms",
                "url": "https://realpython.com/python-for-loop/",
                "format": "text",
                "estimated_time": 20,
                "difficulty": "easy",
            },
            {
                "title": "HackerRank: Loops Practice Challenges",
                "url": "https://www.hackerrank.com/domains/python?filters%5Bsubdomains%5D%5B%5D=py-introduction",
                "format": "practice",
                "estimated_time": 30,
                "difficulty": "easy",
            },
            {
                "title": "VisuAlgo: Interactive Loop Stepper & Visualization",
                "url": "https://visualgo.net/en",
                "format": "interactive",
                "estimated_time": 25,
                "difficulty": "easy",
            },
        ],
    },
    # 2. Arrays
    {
        "topic": "Arrays",
        "resources": [
            {
                "title": "Arrays & Dynamic Arrays in 10 Minutes",
                "url": "https://www.youtube.com/watch?v=pmN9ExfY3yU",
                "format": "video",
                "estimated_time": 20,
                "difficulty": "easy",
            },
            {
                "title": "Array Data Structure - GeeksforGeeks Guide",
                "url": "https://www.geeksforgeeks.org/array-data-structure-guide/",
                "format": "text",
                "estimated_time": 25,
                "difficulty": "easy",
            },
            {
                "title": "LeetCode: Two Sum & Basic Array Problems",
                "url": "https://leetcode.com/tag/array/",
                "format": "practice",
                "estimated_time": 35,
                "difficulty": "easy",
            },
            {
                "title": "Interactive Memory Layout & Array Indexing Explorer",
                "url": "https://visualgo.net/en/array",
                "format": "interactive",
                "estimated_time": 25,
                "difficulty": "easy",
            },
        ],
    },
    # 3. Strings
    {
        "topic": "Strings",
        "resources": [
            {
                "title": "String Manipulation & Two Pointers Explained",
                "url": "https://www.youtube.com/watch?v=jNX_mSmcrjM",
                "format": "video",
                "estimated_time": 25,
                "difficulty": "easy",
            },
            {
                "title": "Common String Algorithms and Immutability",
                "url": "https://www.geeksforgeeks.org/string-data-structure/",
                "format": "text",
                "estimated_time": 20,
                "difficulty": "easy",
            },
            {
                "title": "LeetCode: Valid Anagram & Palindrome Practice",
                "url": "https://leetcode.com/tag/string/",
                "format": "practice",
                "estimated_time": 30,
                "difficulty": "easy",
            },
            {
                "title": "Interactive String Matching & Regex Visualizer",
                "url": "https://regex101.com/",
                "format": "interactive",
                "estimated_time": 20,
                "difficulty": "easy",
            },
        ],
    },
    # 4. Recursion
    {
        "topic": "Recursion",
        "resources": [
            {
                "title": "Recursion for Beginners - Call Stack Visualized",
                "url": "https://www.youtube.com/watch?v=Mv9NEXX1VHc",
                "format": "video",
                "estimated_time": 30,
                "difficulty": "medium",
            },
            {
                "title": "Thinking Recursively: Base Cases and Recurrence",
                "url": "https://realpython.com/python-thinking-recursively/",
                "format": "text",
                "estimated_time": 30,
                "difficulty": "medium",
            },
            {
                "title": "LeetCode: Reverse String & Fibonacci Recursion",
                "url": "https://leetcode.com/tag/recursion/",
                "format": "practice",
                "estimated_time": 40,
                "difficulty": "medium",
            },
            {
                "title": "Python Tutor: Step-by-Step Recursive Stack Visualizer",
                "url": "https://pythontutor.com/visualize.html",
                "format": "interactive",
                "estimated_time": 30,
                "difficulty": "medium",
            },
        ],
    },
    # 5. Linked Lists
    {
        "topic": "Linked Lists",
        "resources": [
            {
                "title": "Singly & Doubly Linked Lists in Depth",
                "url": "https://www.youtube.com/watch?v=Hj_rA0dhr2I",
                "format": "video",
                "estimated_time": 35,
                "difficulty": "medium",
            },
            {
                "title": "Linked List Data Structure & Pointer Manipulation",
                "url": "https://www.geeksforgeeks.org/data-structures/linked-list/",
                "format": "text",
                "estimated_time": 25,
                "difficulty": "medium",
            },
            {
                "title": "LeetCode: Reverse Linked List & Merge Two Sorted Lists",
                "url": "https://leetcode.com/tag/linked-list/",
                "format": "practice",
                "estimated_time": 45,
                "difficulty": "medium",
            },
            {
                "title": "VisuAlgo: Interactive Linked List Node Manipulation",
                "url": "https://visualgo.net/en/list",
                "format": "interactive",
                "estimated_time": 30,
                "difficulty": "medium",
            },
        ],
    },
    # 6. Stacks
    {
        "topic": "Stacks",
        "resources": [
            {
                "title": "Stack Data Structure & LIFO Principle Explained",
                "url": "https://www.youtube.com/watch?v=F1F2imiOJfk",
                "format": "video",
                "estimated_time": 25,
                "difficulty": "medium",
            },
            {
                "title": "Monotonic Stacks and Parentheses Matching",
                "url": "https://www.geeksforgeeks.org/stack-data-structure/",
                "format": "text",
                "estimated_time": 25,
                "difficulty": "medium",
            },
            {
                "title": "LeetCode: Valid Parentheses & Min Stack",
                "url": "https://leetcode.com/tag/stack/",
                "format": "practice",
                "estimated_time": 35,
                "difficulty": "medium",
            },
            {
                "title": "Interactive Stack Push/Pop Simulator",
                "url": "https://visualgo.net/en/list",
                "format": "interactive",
                "estimated_time": 20,
                "difficulty": "medium",
            },
        ],
    },
    # 7. Queues
    {
        "topic": "Queues",
        "resources": [
            {
                "title": "Queue & Deque Data Structures Explained",
                "url": "https://www.youtube.com/watch?v=D6gu-_tm9g8",
                "format": "video",
                "estimated_time": 25,
                "difficulty": "medium",
            },
            {
                "title": "Circular Queues & BFS Applications",
                "url": "https://www.geeksforgeeks.org/queue-data-structure/",
                "format": "text",
                "estimated_time": 25,
                "difficulty": "medium",
            },
            {
                "title": "LeetCode: Implement Queue using Stacks",
                "url": "https://leetcode.com/tag/queue/",
                "format": "practice",
                "estimated_time": 35,
                "difficulty": "medium",
            },
            {
                "title": "Interactive Queue Enqueue/Dequeue Animator",
                "url": "https://visualgo.net/en/list",
                "format": "interactive",
                "estimated_time": 20,
                "difficulty": "medium",
            },
        ],
    },
    # 8. Sorting
    {
        "topic": "Sorting",
        "resources": [
            {
                "title": "Merge Sort & Quick Sort Divide-and-Conquer",
                "url": "https://www.youtube.com/watch?v=4VqmGXwpLqc",
                "format": "video",
                "estimated_time": 35,
                "difficulty": "medium",
            },
            {
                "title": "Sorting Algorithms Complexity & Tradeoffs Comparison",
                "url": "https://www.geeksforgeeks.org/sorting-algorithms/",
                "format": "text",
                "estimated_time": 30,
                "difficulty": "medium",
            },
            {
                "title": "LeetCode: Sort an Array & Kth Largest Element",
                "url": "https://leetcode.com/tag/sorting/",
                "format": "practice",
                "estimated_time": 45,
                "difficulty": "medium",
            },
            {
                "title": "Interactive Sorting Algorithm Visualizer",
                "url": "https://visualgo.net/en/sorting",
                "format": "interactive",
                "estimated_time": 30,
                "difficulty": "medium",
            },
        ],
    },
    # 9. Searching
    {
        "topic": "Searching",
        "resources": [
            {
                "title": "Binary Search Algorithm in 10 Minutes",
                "url": "https://www.youtube.com/watch?v=fDKIpRe8GW4",
                "format": "video",
                "estimated_time": 20,
                "difficulty": "easy",
            },
            {
                "title": "Binary Search Invariants and Common Pitfalls",
                "url": "https://www.geeksforgeeks.org/binary-search/",
                "format": "text",
                "estimated_time": 20,
                "difficulty": "easy",
            },
            {
                "title": "LeetCode: Binary Search & Search Insert Position",
                "url": "https://leetcode.com/tag/binary-search/",
                "format": "practice",
                "estimated_time": 30,
                "difficulty": "easy",
            },
            {
                "title": "Interactive Binary Search Stepper",
                "url": "https://visualgo.net/en/bst",
                "format": "interactive",
                "estimated_time": 20,
                "difficulty": "easy",
            },
        ],
    },
    # 10. Trees
    {
        "topic": "Trees",
        "resources": [
            {
                "title": "Binary Trees & BST Traversals (Inorder, Preorder, Postorder)",
                "url": "https://www.youtube.com/watch?v=fAAZ23XdMt8",
                "format": "video",
                "estimated_time": 45,
                "difficulty": "hard",
            },
            {
                "title": "Comprehensive Guide to Tree Data Structures",
                "url": "https://www.geeksforgeeks.org/binary-tree-data-structure/",
                "format": "text",
                "estimated_time": 35,
                "difficulty": "hard",
            },
            {
                "title": "LeetCode: Maximum Depth of Binary Tree & Invert Binary Tree",
                "url": "https://leetcode.com/tag/tree/",
                "format": "practice",
                "estimated_time": 50,
                "difficulty": "hard",
            },
            {
                "title": "VisuAlgo: Interactive BST Insertion, Deletion & Traversal",
                "url": "https://visualgo.net/en/bst",
                "format": "interactive",
                "estimated_time": 35,
                "difficulty": "hard",
            },
        ],
    },
    # 11. Hashing
    {
        "topic": "Hashing",
        "resources": [
            {
                "title": "Hash Tables & Collision Resolution Strategies",
                "url": "https://www.youtube.com/watch?v=KyUTuwz_b7Q",
                "format": "video",
                "estimated_time": 35,
                "difficulty": "hard",
            },
            {
                "title": "Hash Map Internals & Load Factors Explained",
                "url": "https://www.geeksforgeeks.org/hashing-data-structure/",
                "format": "text",
                "estimated_time": 30,
                "difficulty": "hard",
            },
            {
                "title": "LeetCode: Group Anagrams & Subarray Sum Equals K",
                "url": "https://leetcode.com/tag/hash-table/",
                "format": "practice",
                "estimated_time": 45,
                "difficulty": "hard",
            },
            {
                "title": "Interactive Hash Table & Collision Explorer",
                "url": "https://visualgo.net/en/hashtable",
                "format": "interactive",
                "estimated_time": 30,
                "difficulty": "hard",
            },
        ],
    },
]


def seed_resources():
    db = SessionLocal()
    print("Seeding curated learning resources...")
    added_count = 0
    existing_count = 0

    try:
        for item in RESOURCE_DEFINITIONS:
            topic_name = item["topic"]
            topic = db.query(Topic).filter(Topic.name == topic_name).first()
            if not topic:
                print(f"Warning: Topic '{topic_name}' not found in database. Skipping.")
                continue

            for res in item["resources"]:
                # Idempotency check by (topic_id, title, format)
                existing = (
                    db.query(LearningResource)
                    .filter(
                        LearningResource.topic_id == topic.id,
                        LearningResource.title == res["title"],
                        LearningResource.format == res["format"],
                    )
                    .first()
                )
                if not existing:
                    new_res = LearningResource(
                        topic_id=topic.id,
                        title=res["title"],
                        url=res["url"],
                        format=res["format"],
                        estimated_time=res["estimated_time"],
                        difficulty=res["difficulty"],
                    )
                    db.add(new_res)
                    added_count += 1
                else:
                    existing_count += 1

        db.commit()
        print(f"Learning resources seeded successfully: {added_count} added, {existing_count} already existed.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding learning resources: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_resources()
