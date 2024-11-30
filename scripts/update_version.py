#!/usr/bin/env python3
"""
Update version numbers across the project.
Usage: python scripts/update_version.py [new_version]
Example: python scripts/update_version.py 0.1.2
"""

import sys
import re
from pathlib import Path
import fileinput

def read_env_version(env_file: Path) -> str:
    """Read version from an env file."""
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('APP_VERSION='):
                    return line.split('=')[1].strip()
    return None

def update_version(new_version):
    # Update version.py
    version_file = Path("app/version.py")
    with fileinput.FileInput(version_file, inplace=True) as file:
        for line in file:
            if line.startswith('VERSION = '):
                print(f'VERSION = "{new_version}"')
            else:
                print(line, end='')

    # Update health.py
    health_file = Path("app/health.py")
    if health_file.exists():
        with fileinput.FileInput(health_file, inplace=True) as file:
            for line in file:
                if 'version="' in line and 'HealthResponse(' in line:
                    # Replace version in HealthResponse instantiation
                    print(re.sub(r'version="[^"]*"', f'version="{new_version}"', line), end='')
                else:
                    print(line, end='')

    # Update .env.example
    env_example = Path(".env.example")
    if env_example.exists():
        with fileinput.FileInput(env_example, inplace=True) as file:
            for line in file:
                if line.startswith('APP_VERSION='):
                    print(f'APP_VERSION={new_version}')
                else:
                    print(line, end='')

    # Update CHANGELOG.md
    changelog = Path("CHANGELOG.md")
    if changelog.exists():
        with open(changelog, 'r') as f:
            content = f.read()
        
        if f"## [{new_version}]" not in content:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            new_section = f"\n## [{new_version}] - {today}\n\n### Added\n\n### Changed\n\n### Fixed\n\n"
            
            # Add after the first line (title)
            lines = content.split('\n')
            lines.insert(2, new_section)
            
            with open(changelog, 'w') as f:
                f.write('\n'.join(lines))

    # Check .env if it exists
    env_file = Path(".env")
    if env_file.exists():
        env_version = read_env_version(env_file)
        if env_version and env_version != new_version:
            print(f"\nWARNING: Your .env file contains version {env_version}")
            print(f"Please update APP_VERSION={new_version} in your .env file")

    print(f"Updated version to {new_version}")
    print("\nFiles updated:")
    print("- app/version.py")
    print("- app/health.py")
    print("- .env.example")
    print("- CHANGELOG.md")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_version.py [new_version]")
        sys.exit(1)
    
    new_version = sys.argv[1]
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("Version must be in format X.Y.Z")
        sys.exit(1)
    
    update_version(new_version)