import asyncio
from typing import Optional, List, Dict, Any
import random
from datetime import datetime
import faker
import json
from pathlib import Path
import cProfile
import pstats
import io
from contextlib import contextmanager
import time
import os

from app.models import Thing, Story, Relationship
from app.schemas import ThingCreate, StoryCreate, RelationshipCreate
from app.logger import setup_logger

logger = setup_logger(__name__)
fake = faker.Faker()

class DevTools:
    def __init__(self):
        self.profile_dir = Path("/src/profiles")
        self.profile_dir.mkdir(exist_ok=True)
        
    async def generate_test_data(
        self,
        num_things: int = 10,
        num_stories_per_thing: int = 2,
        num_relationships: int = 5
    ):
        """Generate test data for development."""
        try:
            # Generate things
            things = await self._generate_things(num_things)
            
            # Generate stories
            stories = []
            for thing in things:
                thing_stories = await self._generate_stories(thing, num_stories_per_thing)
                stories.extend(thing_stories)
            
            # Generate relationships
            relationships = await self._generate_relationships(things, num_relationships)
            
            return {
                "things": things,
                "stories": stories,
                "relationships": relationships
            }
            
        except Exception as e:
            logger.error(f"Failed to generate test data: {str(e)}")
            raise

    @contextmanager
    def profile_code(self, name: str):
        """Profile code execution."""
        profiler = cProfile.Profile()
        profiler.enable()
        start_time = time.time()
        
        try:
            yield
        finally:
            profiler.disable()
            duration = time.time() - start_time
            
            # Save profile results
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            profile_path = self.profile_dir / f"{name}_{timestamp}.prof"
            
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats()
            
            with open(profile_path, 'w') as f:
                f.write(f"Duration: {duration:.2f} seconds\n\n")
                f.write(s.getvalue())

    async def _generate_things(self, count: int) -> List[Thing]:
        """Generate test things."""
        things = []
        types = ["appliance", "electronics", "furniture", "tool"]
        materials = ["steel", "aluminum", "plastic", "wood", "glass", "copper"]
        
        for _ in range(count):
            thing = ThingCreate(
                type=random.choice(types),
                name={
                    "default": fake.product_name(),
                    "translations": {
                        "es": fake.product_name(),
                        "de": fake.product_name()
                    }
                },
                manufacturer={
                    "name": fake.company(),
                    "website": fake.url(),
                    "contact": fake.email()
                },
                properties={
                    "dimensions": {
                        "length": random.uniform(10, 100),
                        "width": random.uniform(10, 100),
                        "height": random.uniform(10, 100)
                    },
                    "materials": random.sample(materials, random.randint(1, 3)),
                    "serial_number": fake.uuid4()
                }
            )
            things.append(thing)
        
        return things

    async def _generate_stories(self, thing: Thing, count: int) -> List[Story]:
        """Generate test repair stories."""
        stories = []
        story_types = ["repair", "maintenance", "modification"]
        tools = ["screwdriver", "pliers", "wrench", "hammer", "multimeter"]
        
        for _ in range(count):
            steps = []
            for i in range(random.randint(3, 7)):
                steps.append({
                    "order": i + 1,
                    "description": {
                        "default": fake.paragraph(),
                        "translations": {
                            "es": fake.paragraph(),
                            "de": fake.paragraph()
                        }
                    },
                    "warnings": [fake.sentence() for _ in range(random.randint(0, 2))],
                    "tools": random.sample(tools, random.randint(1, 3))
                })
            
            story = StoryCreate(
                thing_id=thing.id,
                type=random.choice(story_types),
                procedure=steps
            )
            stories.append(story)
        
        return stories

    async def _generate_relationships(self, things: List[Thing], count: int) -> List[Relationship]:
        """Generate test relationships between things."""
        relationships = []
        relationship_types = ["component", "accessory", "tool", "compatible"]
        
        for _ in range(count):
            source = random.choice(things)
            target = random.choice(things)
            if source != target:
                relationship = RelationshipCreate(
                    thing_id=source.id,
                    relationship_type=random.choice(relationship_types),
                    target_uri=target.uri,
                    relation_metadata={
                        "required": random.choice([True, False]),
                        "quantity": random.randint(1, 5)
                    }
                )
                relationships.append(relationship)
        
        return relationships

    def setup_development_environment(self):
        """Setup development environment."""
        # Implementation here
        pass
