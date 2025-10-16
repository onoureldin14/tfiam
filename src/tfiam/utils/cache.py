"""Caching utilities for AI responses."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class AIResponseCache:
    """File-based cache for AI responses to reduce API costs."""

    def __init__(self, cache_dir: str = ".tfiam-cache"):
        """Initialize the cache with a specified directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "ai_responses.json"
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache data from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, UnicodeDecodeError):
                # If cache file is corrupted or has encoding issues, start fresh
                try:
                    # Try to load with ASCII encoding as fallback
                    with open(self.cache_file, "r", encoding="ascii") as f:
                        return json.load(f)
                except Exception:
                    # If all else fails, start fresh
                    return {}
        return {}

    def _save_cache(self) -> None:
        """Save cache data to file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except (IOError, UnicodeEncodeError) as e:
            print(f"Warning: Could not save cache: {e}")
            # Try to save with ASCII encoding as fallback
            try:
                with open(self.cache_file, "w", encoding="ascii") as f:
                    json.dump(self.cache_data, f, indent=2, ensure_ascii=True)
            except Exception as fallback_e:
                print(f"Warning: Cache save failed completely: {fallback_e}")

    def _generate_cache_key(self, data: Dict[str, Any], cache_type: str = "statement") -> str:
        """Generate a cache key based on data content and type."""
        if cache_type == "statement":
            # Create a normalized representation of the statement
            normalized_data = {
                "type": "statement",
                "sid": data.get("sid", ""),
                "effect": data.get("effect", ""),
                "actions": sorted(data.get("action", [])),
                "resources": sorted(data.get("resource", [])),
            }
        elif cache_type == "optimization":
            # Create a normalized representation of the optimization request
            normalized_data = {
                "type": "optimization",
                "terraform_resources": sorted(data.get("terraform_resources", [])),
                "policy_statements": sorted(data.get("policy_statements", [])),
                "verification_analysis": data.get("verification_analysis", ""),
            }
        elif cache_type == "verification":
            # Create a normalized representation of the verification request
            normalized_data = {
                "type": "verification",
                "terraform_resources": sorted(data.get("terraform_resources", [])),
                "policy_statements": sorted(data.get("policy_statements", [])),
                "terraform_content_hash": hashlib.sha256(
                    data.get("terraform_content", "").encode()
                ).hexdigest()[:8],
            }
        else:
            # Generic fallback
            normalized_data = {"type": cache_type, "data": data}

        # Create a hash of the normalized data
        data_str = json.dumps(normalized_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]  # Use first 16 chars

    def get(self, data: Dict[str, Any], cache_type: str = "statement") -> Optional[str]:
        """Get cached AI response for data."""
        cache_key = self._generate_cache_key(data, cache_type)
        return self.cache_data.get(cache_key)

    def set(self, data: Dict[str, Any], response: str, cache_type: str = "statement") -> None:
        """Cache an AI response for data."""
        cache_key = self._generate_cache_key(data, cache_type)
        self.cache_data[cache_key] = response
        self._save_cache()

    def get_optimization(self, optimization_data: Dict[str, Any]) -> Optional[str]:
        """Get cached optimization response."""
        return self.get(optimization_data, "optimization")

    def set_optimization(self, optimization_data: Dict[str, Any], response: str) -> None:
        """Cache an optimization response."""
        self.set(optimization_data, response, "optimization")

    def get_verification(self, verification_data: Dict[str, Any]) -> Optional[str]:
        """Get cached verification response."""
        return self.get(verification_data, "verification")

    def set_verification(self, verification_data: Dict[str, Any], response: str) -> None:
        """Cache a verification response."""
        self.set(verification_data, response, "verification")

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache_data = {}
        if self.cache_file.exists():
            self.cache_file.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache_data),
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
            "cache_dir": str(self.cache_dir),
        }
