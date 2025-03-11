import os

UPDATE = os.environ.get("GOLDIE_UPDATE", "false").lower() in ["true", "1"]
"""
Whether to update the golden files.
"""
