"""Test configuration file path resolution."""

from pathlib import Path
from deerflow.config.app_config import AppConfig

print("="*60)
print("Configuration Path Resolution Test")
print("="*60)

print("\nCurrent working directory:")
print(f"  {Path.cwd()}")

print("\nResolving config path:")
try:
    config_path = AppConfig.resolve_config_path()
    print(f"  Resolved path: {config_path}")
    print(f"  Exists: {config_path.exists()}")
except FileNotFoundError as e:
    print(f"  Error: {e}")

print("\nChecking parent directory:")
parent_config = Path.cwd().parent / "config.yaml"
print(f"  Path: {parent_config}")
print(f"  Exists: {parent_config.exists()}")

print("\nChecking backend directory:")
backend_config = Path.cwd() / "config.yaml"
print(f"  Path: {backend_config}")
print(f"  Exists: {backend_config.exists()}")

print("\n" + "="*60)