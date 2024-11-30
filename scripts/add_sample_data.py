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

def create_story(thing_id, data):
    """Create a repair story for a thing."""
    data["thing_id"] = thing_id
    response = requests.post(f"{BASE_URL}/api/v1/stories", json=data)
    if response.status_code == 200:
        logger.info(f"Created story for thing {thing_id}")
    else:
        logger.error(f"Failed to create story: {response.text}")
        raise Exception(f"Failed to create story: {response.text}")

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

    # Create relationships
    create_relationship(
        laptop_id, 
        battery_id,
        "has_component",
        {"position": "bottom", "removable": True}
    )
    
    create_relationship(
        laptop_id,
        display_id,
        "has_component",
        {"position": "lid", "removable": True}
    )

    create_relationship(
        battery_id,
        display_id,
        "powers",
        {"voltage": "15.4V"}
    )

    # Create stories
    # 1. Battery Replacement Story
    battery_story = {
        "type": "repair",
        "procedure": [
            {
                "order": 1,
                "description": {
                    "default": "Turn off laptop and disconnect power"
                },
                "warnings": ["Ensure laptop is powered off"],
                "tools": ["none"],
                "media": []
            },
            {
                "order": 2,
                "description": {
                    "default": "Flip laptop over and unscrew battery cover"
                },
                "warnings": ["Use correct size screwdriver"],
                "tools": ["Phillips screwdriver"],
                "media": []
            },
            {
                "order": 3,
                "description": {
                    "default": "Lift old battery out and insert new one"
                },
                "warnings": ["Handle battery with care"],
                "tools": ["none"],
                "media": []
            }
        ]
    }
    create_story(laptop_id, battery_story)

    # 2. Display Repair Story
    display_story = {
        "type": "repair",
        "procedure": [
            {
                "order": 1,
                "description": {
                    "default": "Remove display bezel"
                },
                "warnings": ["Work on clean surface"],
                "tools": ["plastic pry tool"],
                "media": []
            },
            {
                "order": 2,
                "description": {
                    "default": "Disconnect display cable"
                },
                "warnings": ["Handle connectors gently"],
                "tools": ["tweezers"],
                "media": []
            },
            {
                "order": 3,
                "description": {
                    "default": "Replace display panel"
                },
                "warnings": ["Align properly before securing"],
                "tools": ["screwdriver"],
                "media": []
            }
        ]
    }
    create_story(display_id, display_story)

    # 3. Laptop Maintenance Story
    laptop_story = {
        "type": "maintenance",
        "procedure": [
            {
                "order": 1,
                "description": {
                    "default": "Clean cooling system"
                },
                "warnings": ["Do not use compressed air"],
                "tools": ["brush", "vacuum"],
                "media": []
            },
            {
                "order": 2,
                "description": {
                    "default": "Check all port modules"
                },
                "warnings": ["Handle modules carefully"],
                "tools": ["none"],
                "media": []
            },
            {
                "order": 3,
                "description": {
                    "default": "Update firmware"
                },
                "warnings": ["Do not interrupt process"],
                "tools": ["none"],
                "media": []
            }
        ]
    }
    create_story(laptop_id, laptop_story)

if __name__ == "__main__":
    main()
