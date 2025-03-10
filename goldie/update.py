import os

UPDATE = os.environ.get("GOLDIE_UPDATE", "false").lower() == "true"
"""
Whether to update the golden files.
"""
