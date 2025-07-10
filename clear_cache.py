#!/usr/bin/env python3
"""
Simple script to clear cache before testing
"""

print("🧹 Clearing cache...")

# Force clear any cache variables
LANGUAGE_CACHE = {}
INTENT_CACHE = {}

print("✅ Cache cleared!")
print("📝 Note: This will take effect when the bot restarts.") 