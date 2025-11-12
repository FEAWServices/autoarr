#!/usr/bin/env python3
"""Script to check license compatibility of all dependencies with GPL-3.0."""

import subprocess
import json
import sys

# GPL-3.0 compatible licenses
GPL_COMPATIBLE_LICENSES = {
    'MIT', 'MIT License',
    'BSD', 'BSD License', 'BSD-2-Clause', 'BSD-3-Clause', '3-Clause BSD License',
    'Apache', 'Apache License 2.0', 'Apache Software License', 'Apache-2.0',
    'GPL', 'GPL-2.0', 'GPL-3.0', 'GPL-3.0-or-later', 'GPLv3',
    'LGPL', 'LGPL-2.1', 'LGPL-3.0', 'LGPLv3',
    'Python Software Foundation License', 'PSF',
    'ISC', 'ISC License',
    'MPL', 'MPL-2.0', 'Mozilla Public License 2.0',
    'Unlicense', 'Public Domain',
    'HPND', 'Historical Permission Notice and Disclaimer',
}

# Potentially problematic licenses (need review)
REVIEW_NEEDED = {
    'UNKNOWN',
    'Proprietary',
}


def get_installed_packages():
    """Get list of installed packages with their licenses."""
    try:
        result = subprocess.run(
            ['pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ Error getting package list: {e}")
        return []


def get_package_license(package_name):
    """Get license for a specific package."""
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            capture_output=True,
            text=True,
            check=True
        )

        for line in result.stdout.split('\n'):
            if line.startswith('License:'):
                return line.split(':', 1)[1].strip()

        return 'UNKNOWN'
    except Exception:
        return 'UNKNOWN'


def check_license_compatibility(license_name):
    """Check if a license is GPL-3.0 compatible."""
    if not license_name or license_name == 'UNKNOWN':
        return 'REVIEW'

    # Check exact matches
    if license_name in GPL_COMPATIBLE_LICENSES:
        return 'COMPATIBLE'

    # Check partial matches (case-insensitive)
    license_lower = license_name.lower()
    for compatible in GPL_COMPATIBLE_LICENSES:
        if compatible.lower() in license_lower:
            return 'COMPATIBLE'

    # Check if it needs review
    for review in REVIEW_NEEDED:
        if review.lower() in license_lower:
            return 'REVIEW'

    return 'REVIEW'


def main():
    """Main function to check all package licenses."""
    print("🔍 Checking GPL-3.0 license compatibility of Python dependencies...\n")

    packages = get_installed_packages()

    if not packages:
        print("❌ No packages found")
        sys.exit(1)

    print(f"Found {len(packages)} packages\n")

    compatible = []
    review_needed = []

    for pkg in packages:
        name = pkg['name']
        version = pkg['version']
        license_name = get_package_license(name)
        status = check_license_compatibility(license_name)

        if status == 'COMPATIBLE':
            compatible.append((name, version, license_name))
            print(f"✅ {name:30} {version:15} {license_name}")
        else:
            review_needed.append((name, version, license_name))
            print(f"⚠️  {name:30} {version:15} {license_name}")

    print(f"\n📊 Summary:")
    print(f"   ✅ GPL-3.0 Compatible: {len(compatible)}")
    print(f"   ⚠️  Needs Review: {len(review_needed)}")
    print(f"   📦 Total Packages: {len(packages)}")

    if review_needed:
        print(f"\n⚠️  Packages that need license review:")
        for name, version, license_name in review_needed:
            print(f"   - {name} ({version}): {license_name}")
        print(f"\nNote: 'UNKNOWN' licenses typically means the package metadata doesn't")
        print(f"specify a license, but most Python packages are MIT/BSD/Apache licensed.")
        print(f"You can check each package's repository for license information.")
    else:
        print(f"\n🎉 All dependencies are GPL-3.0 compatible!")

    return 0 if not review_needed else 1


if __name__ == '__main__':
    sys.exit(main())
