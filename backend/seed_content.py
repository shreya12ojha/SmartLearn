from app.database import SessionLocal
from app.models import Topic
from app.content_models import ContentResource

db = SessionLocal()

catalog = {
    "Loops": [
        {
            "title": "Python Loops Tutorial",
            "url": "https://www.youtube.com/",
            "platform": "YouTube",
            "format": "video",
            "difficulty": "Beginner",
            "estimated_minutes": 15,
            "description": "Learn for-loops, while-loops, and control statements.",
        },
        {
            "title": "Loops in Python",
            "url": "https://www.geeksforgeeks.org/python/python-loops/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Beginner",
            "estimated_minutes": 10,
            "description": "Quick written explanation with examples.",
        },
    ],

    "Arrays": [
        {
            "title": "Arrays - Data Structures",
            "url": "https://www.geeksforgeeks.org/dsa/array-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Beginner",
            "estimated_minutes": 15,
            "description": "Array basics, operations, and complexity.",
        },
        {
            "title": "Array Practice Problems",
            "url": "https://leetcode.com/tag/array/",
            "platform": "LeetCode",
            "format": "practice",
            "difficulty": "Intermediate",
            "estimated_minutes": 30,
            "description": "Practice array concepts through coding problems.",
        },
    ],

    "Strings": [
        {
            "title": "String Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/string-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Beginner",
            "estimated_minutes": 15,
            "description": "String operations and common interview concepts.",
        }
    ],

    "Recursion": [
        {
            "title": "Recursion Tutorial",
            "url": "https://www.geeksforgeeks.org/dsa/recursion-algorithms/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Intermediate",
            "estimated_minutes": 20,
            "description": "Base cases, recursive calls, and examples.",
        }
    ],

    "Linked Lists": [
        {
            "title": "Linked List Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/linked-list-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Intermediate",
            "estimated_minutes": 20,
            "description": "Linked-list traversal, insertion, and deletion.",
        }
    ],

    "Stacks": [
        {
            "title": "Stack Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/stack-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Intermediate",
            "estimated_minutes": 15,
            "description": "LIFO operations and stack applications.",
        }
    ],

    "Queues": [
        {
            "title": "Queue Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/queue-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Intermediate",
            "estimated_minutes": 15,
            "description": "FIFO operations and queue applications.",
        }
    ],

    "Sorting": [
        {
            "title": "Sorting Algorithms",
            "url": "https://www.geeksforgeeks.org/dsa/sorting-algorithms/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Intermediate",
            "estimated_minutes": 25,
            "description": "Comparison of sorting algorithms and complexities.",
        }
    ],

    "Searching": [
        {
            "title": "Searching Algorithms",
            "url": "https://www.geeksforgeeks.org/dsa/searching-algorithms/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Beginner",
            "estimated_minutes": 15,
            "description": "Linear search and binary search fundamentals.",
        }
    ],

    "Trees": [
        {
            "title": "Tree Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/tree-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Advanced",
            "estimated_minutes": 25,
            "description": "Tree terminology, traversal, and binary trees.",
        }
    ],

    "Hashing": [
        {
            "title": "Hashing Data Structure",
            "url": "https://www.geeksforgeeks.org/dsa/hashing-data-structure/",
            "platform": "GeeksForGeeks",
            "format": "article",
            "difficulty": "Advanced",
            "estimated_minutes": 20,
            "description": "Hash tables, collisions, and complexity.",
        }
    ],
}

added = 0

for topic_name, resources in catalog.items():
    topic = db.query(Topic).filter(Topic.name == topic_name).first()

    if not topic:
        print(f"Skipped: topic '{topic_name}' does not exist.")
        continue

    for resource in resources:
        already_exists = db.query(ContentResource).filter(
            ContentResource.topic_id == topic.id,
            ContentResource.title == resource["title"],
        ).first()

        if already_exists:
            continue

        db.add(ContentResource(topic_id=topic.id, **resource))
        added += 1

db.commit()
db.close()

print(f"Added {added} new content resources.")