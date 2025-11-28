# Markdown Documentation Organization Task

I need you to reorganize all markdown files in this repository following these
specific rules and best practices.

## Core Requirements

1. **Root Directory Cleanup**

   - KEEP in root: Only README.md, claude.md, AGENTS.md and contributing.md
   - MOVE everything else: All other .md files should be relocated to
     appropriate /docs folders

2. **Monolith Monorepo Structure**

   - **Platform-level docs**: `/docs/` (architecture, infrastructure, monorepo guides)
   - **Monolith app docs**: `apps/monolith/docs/` (shared monolith configuration, deployment)
   - **Individual app docs**: `apps/monolith/src/app/{app}/docs/` (app-specific features, design)
     - `apps/monolith/src/app/research/docs/`
     - `apps/monolith/src/app/receipts/docs/`
     - `apps/monolith/src/app/proposals/docs/`
     - `apps/monolith/src/app/books/docs/`
     - `apps/monolith/src/app/admin/docs/`
     - `apps/monolith/src/app/subscriptions/docs/`
   - **Standalone app docs**: `apps/{app}/docs/` (for non-monolith apps if any)
   - **Shared package docs**: `packages/{package}/` (README.md only, keep concise)

3. **Infrastructure Documentation Exception**

   - Infrastructure has docs in TWO locations with clear separation:

   **`/infrastructure/`** - IaC Code + Design Docs

   - KEEP: `README.md` (must be concise, 200-350 lines max)
   - KEEP: `TERRAFORM-*.md` (Terraform-specific documentation)
   - KEEP: `docs/` subdirectory (architecture designs only - immutable)
     - ARCHITECTURE-SUMMARY.md
     - AZURE-ARCHITECTURE.md
     - NETWORK-ARCHITECTURE.md
     - COST-ANALYSIS.md
     - SECURITY-ARCHITECTURE.md
     - DEPLOYMENT-STRATEGY.md

   **`/docs/infrastructure/`** - Operational Guides (frequently updated)

   - `guides/` - Step-by-step HOW-TO guides (prerequisites, quick-start,
     troubleshooting, monitoring, disaster-recovery)
   - `deployment/` - Specific deployment scenarios (B2C, GitOps, CI/CD, staging,
     subdomain)
   - `security/` - Security checklists and procedures

   **Rules**:

   - Design docs stay in `/infrastructure/docs/` (rarely change after initial
     design)
   - Operational guides go in `/docs/infrastructure/` (updated frequently)
   - `/infrastructure/README.md` must be concise with cross-references to
     `/docs/infrastructure/`
   - Do NOT duplicate content - use cross-references instead

4. **Document Archival**
   - Review all markdown files for relevance
   - Move temporary/tactical/outdated docs to `/docs/_archive/` folders
   - Keep only actively useful documentation in main `/docs/` folders
   - Preserve folder structure in archives (e.g.,
     `/docs/_archive/2024/sprint-notes/`)

## Additional Best Practices to Implement

5. **Standardize Naming Conventions**

   - Use lowercase with hyphens: `api-guide.md` not `API_Guide.md`
   - Add dates to archived files: `_archive/2024-01-15-old-setup.md`
   - Use clear, descriptive names: `database-schema.md` not `db.md`

6. **Create Index Files**

   - Add a `README.md` in each `/docs/` folder
   - Include a table of contents linking to all documents in that folder
   - Add brief descriptions for each linked document

7. **Categorize by Type** Within each `/docs/` folder, create subdirectories:

   - `/docs/guides/` - How-to guides and tutorials
   - `/docs/api/` - API documentation
   - `/docs/architecture/` - System design and architecture docs
   - `/docs/development/` - Development setup, contributing guides
   - `/docs/deployment/` - Deployment and operations docs
   - `/docs/_archive/` - Outdated/temporary documents

8. **Add Metadata Headers** Ensure each kept document has a YAML front matter header:

   ```markdown
   ---
   title: Document Title
   date: 2024-01-15
   status: active|deprecated|draft
   author: author-name
   ---
   ```

9. **Remove Redundancy**
   - Identify and consolidate duplicate content
   - Merge similar documents where appropriate
   - Delete truly redundant files (after confirming they're in version control)

## Execution Steps

1. First, scan the entire repository to identify all .md files
2. Create necessary directory structures
3. Move files according to the rules above
4. Update the README.md at the root of each docs folder to act as the index
5. Create/update a `/docs/README.md` explaining the new structure
6. Update any internal links that may have broken

## Decision Criteria for Archiving

Archive documents that are:

- Sprint/meeting notes older than 1 month
- Setup guides for deprecated systems
- Draft documents that were never finalized
- Old API documentation for removed endpoints
- Temporary troubleshooting notes
- POC or experiment documentation

Keep documents that are:

- Current API documentation
- Active architecture decisions (ADRs)
- Setup/installation guides for current systems
- Contributing guidelines
- Current deployment procedures

Please proceed step by step, showing me the migration plan first before making any changes.
