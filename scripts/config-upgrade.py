#!/usr/bin/env python3
"""
config-upgrade.py - Upgrade config.yaml to match config.example.yaml
"""

import os
import sys
import shutil
import copy
from pathlib import Path
import yaml

def main():
    REPO_ROOT = Path(__file__).parent.parent
    EXAMPLE = REPO_ROOT / "config.example.yaml"
    
    # Resolve config.yaml location
    CONFIG = None
    if "DEER_FLOW_CONFIG_PATH" in os.environ and os.path.exists(os.environ["DEER_FLOW_CONFIG_PATH"]):
        CONFIG = Path(os.environ["DEER_FLOW_CONFIG_PATH"])
    elif (REPO_ROOT / "backend" / "config.yaml").exists():
        CONFIG = REPO_ROOT / "backend" / "config.yaml"
    elif (REPO_ROOT / "config.yaml").exists():
        CONFIG = REPO_ROOT / "config.yaml"
    
    if not EXAMPLE.exists():
        print(f"✗ config.example.yaml not found at {EXAMPLE}")
        sys.exit(1)
    
    if CONFIG is None:
        print("No config.yaml found — creating from example...")
        shutil.copy2(EXAMPLE, REPO_ROOT / "config.yaml")
        print("OK config.yaml created. Please review and set your API keys.")
        sys.exit(0)
    
    with open(CONFIG, encoding='utf-8') as f:
        raw_text = f.read()
        user = yaml.safe_load(raw_text) or {}
    
    with open(EXAMPLE, encoding='utf-8') as f:
        example = yaml.safe_load(f) or {}
    
    user_version = user.get('config_version', 0)
    example_version = example.get('config_version', 0)
    
    if user_version >= example_version:
        print(f'OK config.yaml is already up to date (version {user_version}).')
        sys.exit(0)
    
    print(f'Upgrading config.yaml: version {user_version} -> {example_version}')
    print()
    
    # Migrations - add version-specific migrations here
    MIGRATIONS = {
        # Add future migrations here if needed
    }
    
    migrated = []
    for version in range(user_version + 1, example_version + 1):
        migration = MIGRATIONS.get(version)
        if not migration:
            continue
        desc = migration.get('description', f'Migration to v{version}')
        for old, new in migration.get('replacements', []):
            if old in raw_text:
                raw_text = raw_text.replace(old, new)
                migrated.append(f'{old} -> {new}')
    
    # Re-parse after text migrations
    user = yaml.safe_load(raw_text) or {}
    
    if migrated:
        print(f'Applied {len(migrated)} migration(s):')
        for m in migrated:
            print(f'  ~ {m}')
        print()
    
    # Merge missing fields
    added = []
    
    def merge(target, source, path=''):
        """Recursively merge source into target, adding missing keys only."""
        for key, value in source.items():
            key_path = f'{path}.{key}' if path else key
            if key not in target:
                target[key] = copy.deepcopy(value)
                added.append(key_path)
            elif isinstance(value, dict) and isinstance(target[key], dict):
                merge(target[key], value, key_path)
    
    merge(user, example)
    
    # Always update config_version
    user['config_version'] = example_version
    
    # Write
    backup = CONFIG.with_suffix('.yaml.bak')
    shutil.copy2(CONFIG, backup)
    print(f'Backed up to {backup.name}')
    
    with open(CONFIG, 'w', encoding='utf-8') as f:
        yaml.dump(user, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    if added:
        print(f'Added {len(added)} new field(s):')
        for a in added:
            print(f'  + {a}')
    
    if not migrated and not added:
        print('No changes needed (version bumped only).')
    
    print()
    print(f'OK config.yaml upgraded to version {example_version}.')
    print('  Please review the changes and set any new required values.')

if __name__ == "__main__":
    main()
