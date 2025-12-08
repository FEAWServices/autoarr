# AutoArr Landing Page Infrastructure

This directory contains the Pulumi IaC for deploying the AutoArr landing page with:

- **Cloudflare Pages** - Static site hosting with global CDN
- **Cloudflare Turnstile** - Bot protection for the interest form
- **Firebase/GCP** - Firestore for storing submissions + Cloud Functions for form handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloudflare Pages                          │
│              (Static HTML/CSS/JS hosting)                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Turnstile Widget                     │   │
│  │              (Bot protection CAPTCHA)                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Form Submission + Turnstile Token
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Firebase Cloud Function                        │
│                (europe-west2 / London)                      │
│                                                             │
│  1. Verify Turnstile token with Cloudflare                 │
│  2. Validate email + interest level                        │
│  3. Check for duplicate submissions                        │
│  4. Store in Firestore                                     │
│  5. Update analytics counters                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Firestore Database                       │
│                                                             │
│  Collections:                                               │
│  - interest_submissions (email, interest, services, etc.)  │
│  - analytics (totals, daily summaries, service popularity) │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Pulumi CLI** - [Install Pulumi](https://www.pulumi.com/docs/install/)
2. **Node.js 20+** - For Pulumi and Cloud Functions
3. **Cloudflare Account** - With API token
4. **Firebase/GCP Project** - With billing enabled

## Quick Start

### 1. Install Dependencies

```bash
# Pulumi infrastructure
cd infrastructure/landing-page
npm install

# Cloud Functions
cd functions
npm install

# Static site
cd ../site
npm install
```

### 2. Configure Pulumi

```bash
# Login to Pulumi (local state or Pulumi Cloud)
pulumi login --local  # or just `pulumi login` for Pulumi Cloud

# Select/create stack
pulumi stack select dev  # or `pulumi stack init dev`

# Set required configuration
pulumi config set autoarr-landing-page:cloudflareAccountId <your-account-id>
pulumi config set autoarr-landing-page:firebaseProjectId <your-project-id>
pulumi config set autoarr-landing-page:domain autoarr.dev

# Set secrets
pulumi config set --secret cloudflare:apiToken <your-api-token>
```

### 3. Deploy Infrastructure

```bash
# Preview changes
pulumi preview

# Deploy
pulumi up
```

### 4. Deploy Cloud Functions

```bash
cd functions

# Set the Turnstile secret (get from Pulumi output)
firebase functions:config:set turnstile.secret_key="$(pulumi stack output turnstileSecretKey --show-secrets)"

# Deploy
firebase deploy --only functions
```

### 5. Update Site Configuration

After deploying, update the site with the actual values:

```bash
# Get Turnstile site key
pulumi stack output turnstileSiteKey

# Get Cloud Function URL
firebase functions:list
```

Update `site/src/index.html`:

- Replace `TURNSTILE_SITE_KEY_PLACEHOLDER` with the actual site key

Update `site/src/main.js`:

- Update `CONFIG.apiEndpoint` with the Cloud Function URL

### 6. Deploy Site

The site will auto-deploy via GitHub if you've configured the Cloudflare Pages GitHub integration.

For manual deployment:

```bash
cd site
npm run build
npx wrangler pages deploy dist --project-name=autoarr-landing
```

## Configuration Reference

### Pulumi Config

| Key                   | Required | Description                          |
| --------------------- | -------- | ------------------------------------ |
| `cloudflare:apiToken` | Yes      | Cloudflare API token (secret)        |
| `cloudflareAccountId` | Yes      | Cloudflare account ID                |
| `firebaseProjectId`   | Yes      | Firebase/GCP project ID              |
| `domain`              | No       | Custom domain (default: autoarr.dev) |

### Cloudflare API Token Permissions

Create an API token with these permissions:

- Account > Cloudflare Pages > Edit
- Account > Cloudflare Turnstile > Edit
- Zone > DNS > Edit (if using custom domain)

### Firebase/GCP Setup

1. Create a new Firebase project or use existing GCP project
2. Enable billing (required for Cloud Functions)
3. Enable these APIs:
   - Firestore
   - Cloud Functions
   - Cloud Build

## Local Development

### Static Site

```bash
cd site
npm run dev
# Open http://localhost:3000
```

### Cloud Functions

```bash
cd functions
npm run serve
# Emulator runs at http://localhost:5001
```

### Testing the Form

For local testing, you can:

1. Use Turnstile in "always passes" test mode during development
2. Point the form to the Firebase emulator

## Outputs

After `pulumi up`, these outputs are available:

| Output                | Description                               |
| --------------------- | ----------------------------------------- |
| `turnstileSiteKey`    | Turnstile widget site key (public)        |
| `turnstileSecretKey`  | Turnstile verification secret (sensitive) |
| `pagesUrl`            | Cloudflare Pages URL                      |
| `pagesProjectName`    | Cloudflare Pages project name             |
| `firebaseProject`     | Firebase project ID                       |
| `functionsBucketName` | GCS bucket for function source            |

## Security Considerations

- **GDPR Compliance**: No IP addresses are stored, data stored in EU region
- **Rate Limiting**: Duplicate submissions within 24h update existing record
- **Bot Protection**: Turnstile prevents automated spam
- **Firestore Rules**: Write-only from Cloud Functions, no client access

## Costs

Estimated monthly costs for low-traffic site:

| Service              | Free Tier                  | Estimated Cost |
| -------------------- | -------------------------- | -------------- |
| Cloudflare Pages     | Unlimited                  | $0             |
| Cloudflare Turnstile | Unlimited                  | $0             |
| Firebase Firestore   | 1GB storage, 50K reads/day | $0             |
| Cloud Functions      | 2M invocations/month       | $0             |

Total: **$0/month** for typical landing page traffic

## Troubleshooting

### Turnstile Not Loading

1. Check domain is added to Turnstile widget domains
2. Verify site key is correctly set in HTML
3. Check browser console for CORS errors

### Form Submissions Failing

1. Check Cloud Function logs: `firebase functions:log`
2. Verify Turnstile secret is correctly set
3. Check Firestore rules allow function to write

### Pulumi Errors

1. Verify API tokens have correct permissions
2. Check GCP project has billing enabled
3. Run `pulumi refresh` to sync state

## GitHub Actions CI/CD

The infrastructure is deployed via GitHub Actions (`.github/workflows/landing-page-infra.yml`).

### Required GitHub Secrets

Configure these secrets in your repository settings (Settings > Secrets and variables > Actions):

| Secret                    | Required | Description                                             | How to Obtain                                                                    |
| ------------------------- | -------- | ------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `PULUMI_ACCESS_TOKEN`     | Yes      | Pulumi Cloud access token                               | [Pulumi Console](https://app.pulumi.com/account/tokens) > Access Tokens > Create |
| `CLOUDFLARE_API_TOKEN`    | Yes      | Cloudflare API token with Pages + Turnstile permissions | Cloudflare Dashboard > My Profile > API Tokens > Create Token                    |
| `CLOUDFLARE_ACCOUNT_ID`   | Yes      | Your Cloudflare account ID                              | Cloudflare Dashboard > any domain > Overview > Account ID (right sidebar)        |
| `FIREBASE_PROJECT_ID`     | Yes      | Firebase/GCP project ID                                 | Firebase Console > Project Settings > Project ID                                 |
| `GCP_SERVICE_ACCOUNT_KEY` | Yes      | GCP service account JSON key                            | GCP Console > IAM > Service Accounts > Create Key (JSON)                         |

### Cloudflare API Token Permissions

Create a Custom Token with:

```
Account:
  - Cloudflare Pages: Edit
  - Cloudflare Turnstile: Edit
  - Account Settings: Read

Zone (if using custom domain):
  - DNS: Edit
```

### GCP Service Account Permissions

Create a service account with these roles:

- `roles/firebase.admin` - Firebase Admin
- `roles/cloudfunctions.admin` - Cloud Functions Admin
- `roles/datastore.owner` - Firestore Admin
- `roles/storage.admin` - Cloud Storage Admin
- `roles/iam.serviceAccountUser` - Service Account User

```bash
# Create service account
gcloud iam service-accounts create autoarr-landing-deployer \
  --display-name="AutoArr Landing Page Deployer"

# Grant roles
PROJECT_ID="your-project-id"
SA_EMAIL="autoarr-landing-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

for ROLE in firebase.admin cloudfunctions.admin datastore.owner storage.admin iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/${ROLE}"
done

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account="${SA_EMAIL}"

# Copy contents of key.json to GCP_SERVICE_ACCOUNT_KEY secret
cat key.json
```

### GitHub Environments

The workflow uses GitHub Environments for deployment protection:

- `dev` - Development environment (auto-deploys on push to main)
- `prod` - Production environment (manual approval recommended)
- `dev-destroy` / `prod-destroy` - Destruction environments (require approval)

Configure environment protection rules in Settings > Environments.

### Workflow Triggers

| Trigger                                                  | Action                          |
| -------------------------------------------------------- | ------------------------------- |
| Push to `main` (paths: `infrastructure/landing-page/**`) | Deploy to `dev`                 |
| Pull request                                             | Preview changes (comment on PR) |
| Manual dispatch: `preview`                               | Show what would change          |
| Manual dispatch: `up`                                    | Deploy to selected environment  |
| Manual dispatch: `destroy`                               | Tear down infrastructure        |

### Running Manually

```bash
# Via GitHub CLI
gh workflow run landing-page-infra.yml -f action=preview -f environment=dev
gh workflow run landing-page-infra.yml -f action=up -f environment=prod
```

## File Structure

```
infrastructure/landing-page/
├── index.ts              # Main Pulumi infrastructure
├── Pulumi.yaml           # Pulumi project config
├── Pulumi.dev.yaml       # Dev stack config
├── package.json          # Pulumi dependencies
├── tsconfig.json         # TypeScript config
├── README.md             # This file
│
├── site/                 # Static landing page
│   ├── src/
│   │   ├── index.html    # Main HTML
│   │   ├── styles.css    # Styles
│   │   ├── main.js       # Form handler
│   │   └── favicon.svg   # Favicon
│   ├── package.json      # Vite build
│   └── vite.config.js    # Vite config
│
└── functions/            # Firebase Cloud Functions
    ├── src/
    │   └── index.ts      # Function handlers
    ├── package.json      # Function dependencies
    ├── tsconfig.json     # TypeScript config
    └── firebase.json     # Firebase config
```
