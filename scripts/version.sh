#!/bin/bash
# Get version from version.py
VERSION=$(python -c "from app.version import VERSION; print(VERSION)")
echo $VERSION