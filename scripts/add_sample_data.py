#!/usr/bin/env python3
"""
Add sample data to ThingData server

Usage:
    From project root: ./scripts/init_sample_data.sh
    Or directly: python scripts/add_sample_data.py
"""

import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def create_thing(data):
    """Create a thing and return its ID."""
    response = requests.post(f"{BASE_URL}/api/v1/things", json=data)
    if response.status_code == 200:
        thing_id = response.json()["id"]
        logger.info(f"Created thing: {data['name']['default']} (ID: {thing_id})")
        return thing_id
    else:
        logger.error(f"Failed to create thing: {response.text}")
        raise Exception(f"Failed to create thing: {response.text}")

def create_relationship(source_id, target_id, rel_type, metadata=None):
    """Create a relationship between two things."""
    data = {
        "thing_id": source_id,
        "relationship_type": rel_type,
        "target_uri": target_id,
        "relation_metadata": metadata or {}
    }
    response = requests.post(f"{BASE_URL}/api/v1/relationships", json=data)
    if response.status_code == 200:
        logger.info(f"Created relationship: {rel_type} between {source_id} and {target_id}")
    else:
        logger.error(f"Failed to create relationship: {response.text}")
        raise Exception(f"Failed to create relationship: {response.text}")

def create_story(data):
    """Create a repair story."""
    response = requests.post(f"{BASE_URL}/api/v1/stories", json=data)
    if response.status_code == 200:
        story_id = response.json()["id"]
        logger.info(f"Created story {story_id}")
        return story_id
    else:
        logger.error(f"Failed to create story: {response.text}")
        raise Exception(f"Failed to create story: {response.text}")

def create_guide(data):
    """Create a guide and return its ID."""
    response = requests.post(f"{BASE_URL}/api/v1/guides", json=data)
    if response.status_code == 200:
        guide_id = response.json()["id"]
        logger.info(f"Created guide: {data['content']['title']['default']} (ID: {guide_id})")
        return guide_id
    else:
        logger.error(f"Failed to create guide: {response.text}")
        raise Exception(f"Failed to create guide: {response.text}")

def create_relationship(source_type: str, source_id: str, target_type: str, target_id: str, 
                       relationship_type: str, direction: str = "bidirectional", metadata: dict = None):
    """Create a relationship between entities."""
    data = {
        "source_type": source_type,
        "source_id": source_id,
        "target_type": target_type,
        "target_id": target_id,
        "relationship_type": relationship_type,
        "direction": direction,
        "metadata": metadata or {}
    }
    response = requests.post(f"{BASE_URL}/api/v1/relationships", json=data)
    if response.status_code == 200:
        logger.info(f"Created relationship: {relationship_type} between {source_type}/{source_id} and {target_type}/{target_id}")
    else:
        logger.error(f"Failed to create relationship: {response.text}")
        raise Exception(f"Failed to create relationship: {response.text}")

def main():
    # 1. Create Laptop
    laptop = {
        "type": "device",
        "name": {
            "default": "Framework Laptop 13"
        },
        "manufacturer": {
            "name": "Framework",
            "website": "https://frame.work",
            "contact": "support@frame.work"
        },
        "properties": {
            "dimensions": {
                "length": 29.6,
                "width": 22.0,
                "height": 1.6
            },
            "materials": ["aluminum", "glass", "plastic"],
            "manufacturing_date": "2023-09-01"
        }
    }
    laptop_id = create_thing(laptop)

    # 2. Create Battery
    battery = {
        "type": "component",
        "name": {
            "default": "55Wh Battery Module"
        },
        "manufacturer": {
            "name": "Framework"
        },
        "properties": {
            "dimensions": {
                "length": 20.0,
                "width": 10.0,
                "height": 1.0
            },
            "materials": ["lithium-ion", "plastic"],
            "capacity": "55Wh"
        }
    }
    battery_id = create_thing(battery)

    # 3. Create Display
    display = {
        "type": "component",
        "name": {
            "default": "13.5\" Display Module"
        },
        "manufacturer": {
            "name": "Framework"
        },
        "properties": {
            "dimensions": {
                "length": 29.0,
                "width": 19.0,
                "height": 0.5
            },
            "materials": ["glass", "plastic", "metal"],
            "resolution": "2256x1504"
        }
    }
    display_id = create_thing(display)

    # Create relationships between things
    create_relationship(
        source_type="thing",
        source_id=laptop_id,
        target_type="thing",
        target_id=battery_id,
        relationship_type="has_component",
        metadata={"position": "bottom", "removable": True}
    )
    
    create_relationship(
        source_type="thing",
        source_id=laptop_id,
        target_type="thing",
        target_id=display_id,
        relationship_type="has_component",
        metadata={"position": "lid", "removable": True}
    )

    # 4. Create general laptop hinge repair guide
    laptop_guide = {
        "thing_category": {
            "category": "laptop",
            "subcategory": "notebook",
            "attributes": {
                "form_factor": "clamshell",
                "size_range": "13-15 inch"
            }
        },
        "type": {
            "primary": "guide",
            "secondary": "repair"
        },
        "content": {
            "title": {
                "default": "General Laptop Hinge Repair Guide"
            },
            "summary": {
                "default": "How to diagnose and repair common laptop hinge issues"
            },
            "requirements": {
                "skills": ["Basic electronics", "Screwdriver usage"],
                "tools": ["Screwdriver set", "Plastic pry tools"],
                "materials": ["Replacement hinges", "Screws"],
                "certifications": []
            },
            "warnings": [
                {
                    "severity": "CAUTION",
                    "message": {
                        "default": "Disconnect battery before starting"
                    }
                }
            ],
            "procedure": [
                {
                    "order": 1,
                    "title": {"default": "Preparation"},
                    "description": {"default": "Backup data and gather tools"}
                },
                {
                    "order": 2,
                    "title": {"default": "Disassembly"},
                    "description": {"default": "Remove screws and separate components"}
                }
            ]
        }
    }

    guide_id = create_guide(laptop_guide)

    # Create relationship between guide and laptop
    create_relationship(
        source_type="guide",
        source_id=guide_id,
        target_type="thing",
        target_id=laptop_id,
        relationship_type="applies_to",
        direction="unidirectional",
        metadata={"compatibility": "verified", "model_specific": False}
    )

    fridge_story = {
        "thing_category": {
            "category": "appliance",
            "subcategory": "refrigerator",
            "attributes": {
                "component": "door",
                "material": "metal"
            }
        },
        "type": "modification",
        "procedure": [
            {
                "order": 1,
                "description": {
                    "default": "Clean and prepare the door surface"
                },
                "warnings": ["Use appropriate safety equipment"],
                "tools": ["Cleaning supplies", "Sandpaper"],
                "media": []
            },
            {
                "order": 2,
                "description": {
                    "default": "Apply magnetic primer"
                },
                "warnings": ["Work in ventilated area"],
                "tools": ["Paint roller", "Primer"],
                "media": []
            }
        ]
    }
    story_id = create_story(fridge_story)

    # Create relationship between story and guide
    create_relationship(
        source_type="story",
        source_id=story_id,
        target_type="guide",
        target_id=guide_id,
        relationship_type="references",
        direction="unidirectional",
        metadata={"context": "similar_technique"}
    )

if __name__ == "__main__":
    main()