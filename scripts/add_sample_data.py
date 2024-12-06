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
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

class SecurityConfig:
    """Security configuration matching server requirements"""
    ALLOWED_THING_TYPES = ["device", "component", "material", "tool"]
    ALLOWED_STORY_TYPES = ["repair", "maintenance", "modification", "diagnosis"]
    ALLOWED_GUIDE_TYPES = ["manual", "tutorial", "specification", "documentation"]
    ALLOWED_RELATIONSHIP_DIRECTIONS = ["unidirectional", "bidirectional"]

def validate_request_data(data: Dict[str, Any]) -> None:
    """Basic validation of request data"""
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    if len(json.dumps(data)) > 10_000_000:  # 10MB limit
        raise ValueError("Data exceeds size limit")

def create_thing(data: Dict[str, Any]) -> str:
    """Create a thing and return its ID."""
    validate_request_data(data)
    
    # Validate thing type
    if data.get("type") not in SecurityConfig.ALLOWED_THING_TYPES:
        raise ValueError(f"Invalid thing type. Allowed types: {SecurityConfig.ALLOWED_THING_TYPES}")

    response = requests.post(
        f"{BASE_URL}/api/v1/things",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        thing_id = response.json()["id"]
        logger.info(f"Created thing: {data['name']['default']} (ID: {thing_id})")
        return thing_id
    else:
        logger.error(f"Failed to create thing: {response.text}")
        raise Exception(f"Failed to create thing: {response.text}")

def create_guide(data: Dict[str, Any]) -> str:
    """Create a guide and return its ID."""
    validate_request_data(data)
    
    # Validate guide type
    if data.get("type", {}).get("primary") not in SecurityConfig.ALLOWED_GUIDE_TYPES:
        raise ValueError(f"Invalid guide type. Allowed types: {SecurityConfig.ALLOWED_GUIDE_TYPES}")

    response = requests.post(
        f"{BASE_URL}/api/v1/guides",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        guide_id = response.json()["id"]
        logger.info(f"Created guide: {data['content']['title']['default']} (ID: {guide_id})")
        return guide_id
    else:
        logger.error(f"Failed to create guide: {response.text}")
        raise Exception(f"Failed to create guide: {response.text}")

def create_story(data: Dict[str, Any]) -> str:
    """Create a repair story."""
    validate_request_data(data)
    
    # Validate story type
    if data.get("type") not in SecurityConfig.ALLOWED_STORY_TYPES:
        raise ValueError(f"Invalid story type. Allowed types: {SecurityConfig.ALLOWED_STORY_TYPES}")

    response = requests.post(
        f"{BASE_URL}/api/v1/stories",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        story_id = response.json()["id"]
        logger.info(f"Created story {story_id}")
        return story_id
    else:
        logger.error(f"Failed to create story: {response.text}")
        raise Exception(f"Failed to create story: {response.text}")

def create_relationship(
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    relationship_type: str,
    direction: str = "unidirectional",
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Create a relationship between entities."""
    if direction not in SecurityConfig.ALLOWED_RELATIONSHIP_DIRECTIONS:
        raise ValueError(f"Invalid direction. Allowed directions: {SecurityConfig.ALLOWED_RELATIONSHIP_DIRECTIONS}")

    data = {
        "source_type": source_type,
        "source_id": source_id,
        "target_type": target_type,
        "target_id": target_id,
        "relationship_type": relationship_type,
        "direction": direction,
        "metadata": metadata or {}
    }
    
    validate_request_data(data)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/relationships",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        logger.info(f"Created relationship: {relationship_type} between {source_type}/{source_id} and {target_type}/{target_id}")
    else:
        logger.error(f"Failed to create relationship: {response.text}")
        raise Exception(f"Failed to create relationship: {response.text}")

def main():
    try:
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
                "primary": "manual",
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

        # Create category-based repair story
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

        logger.info("Sample data creation completed successfully!")

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
