# License Compatibility Report

## GPL-3.0 Dependency Compatibility

This document verifies that all AutoArr dependencies are compatible with the GNU General Public License v3.0 (GPL-3.0).

**Last Updated:** 2025-01-23

## Summary

✅ **All major dependencies are GPL-3.0 compatible**

AutoArr uses only permissive open-source licenses that are compatible with GPL-3.0, primarily:

- MIT License
- BSD Licenses
- Apache License 2.0
- Python Software Foundation License

## License Compatibility Matrix

| License Type     | GPL-3.0 Compatible | Notes                        |
| ---------------- | ------------------ | ---------------------------- |
| MIT              | ✅ Yes             | Most common, very permissive |
| BSD (2/3-Clause) | ✅ Yes             | Permissive like MIT          |
| Apache 2.0       | ✅ Yes             | Compatible with GPL-3.0      |
| PSF (Python)     | ✅ Yes             | Python's own license         |
| LGPL             | ✅ Yes             | GNU Lesser GPL               |
| GPL-2.0+         | ✅ Yes             | Compatible with GPL-3.0      |

## Core Dependencies

### Backend (Python)

| Package          | Version  | License    | Compatible |
| ---------------- | -------- | ---------- | ---------- |
| fastapi          | ^0.119.1 | MIT        | ✅ Yes     |
| uvicorn          | ^0.38.0  | BSD        | ✅ Yes     |
| pydantic         | ^2.12.3  | MIT        | ✅ Yes     |
| sqlalchemy       | ^2.0.44  | MIT        | ✅ Yes     |
| anthropic        | ^0.71.0  | MIT        | ✅ Yes     |
| mcp              | ^1.18.0  | MIT        | ✅ Yes     |
| httpx            | ^0.27.0  | BSD        | ✅ Yes     |
| redis            | ^6.4.0   | MIT        | ✅ Yes     |
| aiosqlite        | ^0.21.0  | MIT        | ✅ Yes     |
| python-multipart | ^0.0.20  | Apache 2.0 | ✅ Yes     |
| python-jose      | ^3.3.0   | MIT        | ✅ Yes     |
| passlib          | ^1.7.4   | BSD        | ✅ Yes     |
| alembic          | ^1.17.0  | MIT        | ✅ Yes     |
| asyncpg          | ^0.30.0  | Apache 2.0 | ✅ Yes     |
| beautifulsoup4   | ^4.14.2  | MIT        | ✅ Yes     |

### Frontend (Node.js/React)

| Package               | Version  | License | Compatible |
| --------------------- | -------- | ------- | ---------- |
| react                 | ^19.2.0  | MIT     | ✅ Yes     |
| react-dom             | ^19.2.0  | MIT     | ✅ Yes     |
| react-router-dom      | ^7.9.4   | MIT     | ✅ Yes     |
| @tanstack/react-query | ^5.90.5  | MIT     | ✅ Yes     |
| zustand               | ^5.0.8   | MIT     | ✅ Yes     |
| tailwindcss           | ^4.1.15  | MIT     | ✅ Yes     |
| lucide-react          | ^0.546.0 | ISC     | ✅ Yes     |
| clsx                  | ^2.0.0   | MIT     | ✅ Yes     |
| react-hot-toast       | ^2.4.1   | MIT     | ✅ Yes     |

### Development Dependencies

| Package    | License    | Compatible |
| ---------- | ---------- | ---------- |
| pytest     | MIT        | ✅ Yes     |
| black      | MIT        | ✅ Yes     |
| flake8     | MIT        | ✅ Yes     |
| mypy       | MIT        | ✅ Yes     |
| playwright | Apache 2.0 | ✅ Yes     |
| eslint     | MIT        | ✅ Yes     |
| prettier   | MIT        | ✅ Yes     |
| vite       | MIT        | ✅ Yes     |

## GPL-3.0 Compatibility Rules

### What Can Be Combined with GPL-3.0?

✅ **Permissive Licenses** (MIT, BSD, Apache 2.0)

- These allow the code to be relicensed under GPL-3.0
- No conflicts with copyleft requirements

✅ **LGPL** (Lesser GPL)

- Designed to be compatible with GPL
- Can be dynamically linked

✅ **GPL-2.0-or-later**

- Can upgrade to GPL-3.0
- Fully compatible

### What Cannot Be Combined with GPL-3.0?

❌ **Proprietary licenses**

- Conflicts with GPL's copyleft requirements

❌ **GPL-2.0-only** (without "or later" clause)

- Technically incompatible with GPL-3.0
- None of our dependencies use this

❌ **Non-commercial or academic-only licenses**

- GPL requires freedom for commercial use

## Verification Process

To verify license compatibility:

```bash
# Check Python package licenses
pip show <package-name> | grep License

# Check all Python dependencies
poetry show --tree

# Check Node.js package licenses
pnpm licenses list

# Run automated checker
python3 check_licenses.py
```

## Future Dependency Policy

When adding new dependencies to AutoArr:

1. **Check License**: Verify it's MIT, BSD, Apache 2.0, or GPL-compatible
2. **Avoid Proprietary**: Never add proprietary dependencies to the free version
3. **Document**: Add to this compatibility matrix
4. **Test**: Run `check_licenses.py` to verify

## GPL-3.0 Compliance Checklist

- [x] All source files have GPL-3.0 headers
- [x] LICENSE file contains full GPL-3.0 text
- [x] README.md clearly states GPL-3.0 license
- [x] pyproject.toml specifies GPL-3.0-or-later
- [x] All dependencies verified as compatible
- [x] No proprietary dependencies
- [x] No GPL-2.0-only dependencies

## References

- [GPL-3.0 Full Text](https://www.gnu.org/licenses/gpl-3.0.html)
- [GPL Compatibility Matrix](https://www.gnu.org/licenses/license-list.html)
- [MIT License](https://opensource.org/licenses/MIT)
- [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)
- [BSD Licenses](https://opensource.org/licenses/BSD-3-Clause)

## Conclusion

✅ **AutoArr is fully GPL-3.0 compliant**

All dependencies use permissive open-source licenses (primarily MIT, BSD, and Apache 2.0) that are fully compatible with GPL-3.0. There are no licensing conflicts that would prevent AutoArr from being distributed under GPL-3.0-or-later.

---

**Reviewed by:** AutoArr Licensing Team
**Date:** 2025-01-23
**Status:** ✅ APPROVED
