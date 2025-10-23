#!/usr/bin/env python3
"""Script to add GPL-3.0 license headers to Python files."""

import os
import sys
from pathlib import Path
from datetime import datetime

# GPL-3.0 header template
GPL_HEADER = """# Copyright (C) {year} AutoArr Contributors
#
# This file is part of AutoArr.
#
# AutoArr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AutoArr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


def has_license_header(content: str) -> bool:
    """Check if file already has a license header."""
    return "GNU General Public License" in content or "GPL" in content[:500]


def add_header_to_file(file_path: Path) -> bool:
    """Add GPL-3.0 header to a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has license
        if has_license_header(content):
            print(f"⏭️  Skipping {file_path} (already has license)")
            return False

        # Preserve shebang and encoding declarations
        lines = content.split('\n')
        header_lines = []
        content_start_idx = 0

        for i, line in enumerate(lines):
            if line.startswith('#!') or line.startswith('# -*- coding:') or line.startswith('# coding:'):
                header_lines.append(line)
                content_start_idx = i + 1
            else:
                break

        # Build new content
        year = datetime.now().year
        new_content_parts = []

        # Add preserved headers (shebang, encoding)
        if header_lines:
            new_content_parts.append('\n'.join(header_lines))
            new_content_parts.append('')  # Blank line

        # Add GPL header
        new_content_parts.append(GPL_HEADER.format(year=year).strip())
        new_content_parts.append('')  # Blank line after license

        # Add original content (skip preserved headers)
        remaining_content = '\n'.join(lines[content_start_idx:]).lstrip('\n')
        new_content_parts.append(remaining_content)

        new_content = '\n'.join(new_content_parts)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Added license to {file_path}")
        return True

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    autoarr_dir = Path('/app/autoarr')

    if not autoarr_dir.exists():
        print(f"Error: {autoarr_dir} does not exist")
        sys.exit(1)

    # Find all Python files
    py_files = list(autoarr_dir.rglob('*.py'))

    print(f"Found {len(py_files)} Python files\n")

    added = 0
    skipped = 0

    for py_file in sorted(py_files):
        if add_header_to_file(py_file):
            added += 1
        else:
            skipped += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Added license headers: {added}")
    print(f"   ⏭️  Skipped (already licensed): {skipped}")
    print(f"   📄 Total files: {len(py_files)}")


if __name__ == '__main__':
    main()
