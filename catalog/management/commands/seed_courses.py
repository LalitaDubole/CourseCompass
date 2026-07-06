"""
U4/U5 - Django management command to seed sample courses into MongoDB.
Run with: python manage.py seed_courses
"""
from django.core.management.base import BaseCommand
from catalog.mongo import get_courses_collection

SAMPLE_COURSES = [
    {"name": "Python For Everybody", "category": "Programming", "skills_taught": ["python"], "rating": 4.7, "duration_weeks": 6, "platform": "Coursera"},
    {"name": "Sql For Data Analysis", "category": "Data", "skills_taught": ["sql"], "rating": 4.5, "duration_weeks": 4, "platform": "Udemy"},
    {"name": "Statistics Fundamentals", "category": "Data", "skills_taught": ["statistics"], "rating": 4.3, "duration_weeks": 5, "platform": "edX"},
    {"name": "Machine Learning A-Z", "category": "AI/ML", "skills_taught": ["machine learning", "python"], "rating": 4.8, "duration_weeks": 10, "platform": "Udemy"},
    {"name": "Pandas & Data Wrangling", "category": "Data", "skills_taught": ["pandas", "python"], "rating": 4.6, "duration_weeks": 3, "platform": "DataCamp"},
    {"name": "Html & Css Crash Course", "category": "Web Dev", "skills_taught": ["html", "css"], "rating": 4.4, "duration_weeks": 3, "platform": "Udemy"},
    {"name": "Javascript Essentials", "category": "Web Dev", "skills_taught": ["javascript"], "rating": 4.5, "duration_weeks": 5, "platform": "freeCodeCamp"},
    {"name": "Django For Beginners", "category": "Web Dev", "skills_taught": ["django", "python", "sql"], "rating": 4.7, "duration_weeks": 6, "platform": "Udemy"},
    {"name": "Power Bi Masterclass", "category": "Data", "skills_taught": ["power bi"], "rating": 4.2, "duration_weeks": 4, "platform": "Coursera"},
    {"name": "Advanced Excel", "category": "Data", "skills_taught": ["excel"], "rating": 4.1, "duration_weeks": 2, "platform": "LinkedIn Learning"},
    {"name": "Java Programming Bootcamp", "category": "Programming", "skills_taught": ["java"], "rating": 4.4, "duration_weeks": 8, "platform": "Udemy"},
    {"name": "Kotlin For Android", "category": "Mobile", "skills_taught": ["kotlin", "android sdk"], "rating": 4.6, "duration_weeks": 6, "platform": "Coursera"},
    {"name": "Android Sdk Deep Dive", "category": "Mobile", "skills_taught": ["android sdk", "xml"], "rating": 4.3, "duration_weeks": 5, "platform": "Udacity"},
    {"name": "Linux Fundamentals", "category": "Systems", "skills_taught": ["linux"], "rating": 4.5, "duration_weeks": 4, "platform": "edX"},
    {"name": "Networking Basics", "category": "Systems", "skills_taught": ["networking"], "rating": 4.2, "duration_weeks": 4, "platform": "Coursera"},
    {"name": "Cryptography Essentials", "category": "Security", "skills_taught": ["cryptography"], "rating": 4.4, "duration_weeks": 5, "platform": "edX"},
    {"name": "Aws Cloud Practitioner", "category": "Cloud", "skills_taught": ["aws", "networking"], "rating": 4.6, "duration_weeks": 6, "platform": "AWS Training"},
    {"name": "Docker & Containers", "category": "Cloud", "skills_taught": ["docker", "linux"], "rating": 4.5, "duration_weeks": 4, "platform": "Udemy"},
    {"name": "Deep Learning Specialization", "category": "AI/ML", "skills_taught": ["deep learning", "tensorflow", "python"], "rating": 4.9, "duration_weeks": 12, "platform": "Coursera"},
    {"name": "Tensorflow In Practice", "category": "AI/ML", "skills_taught": ["tensorflow", "python"], "rating": 4.7, "duration_weeks": 8, "platform": "Coursera"},
]


class Command(BaseCommand):
    help = "Seeds the MongoDB 'courses' collection with sample course data."

    def handle(self, *args, **options):
        collection = get_courses_collection()
        collection.delete_many({})  # clear old sample data first
        result = collection.insert_many(SAMPLE_COURSES)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(result.inserted_ids)} courses into MongoDB."
            )
        )