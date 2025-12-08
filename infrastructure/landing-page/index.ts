import * as pulumi from "@pulumi/pulumi";
import * as cloudflare from "@pulumi/cloudflare";
import * as gcp from "@pulumi/gcp";

// Configuration
const config = new pulumi.Config();
const cloudflareAccountId = config.require("cloudflareAccountId");
const domain = config.get("domain") || "autoarr.dev";
const firebaseProjectId = config.require("firebaseProjectId");

// =============================================================================
// Cloudflare Turnstile Widget
// =============================================================================

const turnstileWidget = new cloudflare.TurnstileWidget("autoarr-turnstile", {
  accountId: cloudflareAccountId,
  name: "AutoArr Landing Page",
  domains: [domain, `www.${domain}`, "localhost"],
  mode: "managed", // Shows challenge only when needed
  botFightMode: false,
  offlabel: false,
});

// =============================================================================
// Cloudflare Pages Project
// =============================================================================

const pagesProject = new cloudflare.PagesProject("autoarr-landing", {
  accountId: cloudflareAccountId,
  name: "autoarr-landing",
  productionBranch: "main",
  buildConfig: {
    buildCommand: "npm run build",
    destinationDir: "dist",
    rootDir: "site",
  },
  source: {
    type: "github",
    config: {
      owner: "your-github-org", // TODO: Update with actual org
      repoName: "autoarr", // TODO: Update with actual repo
      productionBranch: "main",
      deploymentsEnabled: true,
      productionDeploymentEnabled: true,
      previewDeploymentSetting: "custom",
      previewBranchIncludes: ["preview/*", "staging"],
    },
  },
  deploymentConfigs: {
    production: {
      environmentVariables: {
        TURNSTILE_SITE_KEY: turnstileWidget.id,
        FIREBASE_PROJECT_ID: firebaseProjectId,
        NODE_VERSION: "20",
      },
      compatibilityDate: "2024-01-01",
    },
    preview: {
      environmentVariables: {
        TURNSTILE_SITE_KEY: turnstileWidget.id,
        FIREBASE_PROJECT_ID: firebaseProjectId,
        NODE_VERSION: "20",
      },
      compatibilityDate: "2024-01-01",
    },
  },
});

// =============================================================================
// Cloudflare DNS (if you have a zone)
// =============================================================================

// Uncomment if you have a Cloudflare zone for your domain
// const zone = cloudflare.getZone({ name: domain, accountId: cloudflareAccountId });
//
// const rootRecord = new cloudflare.Record("autoarr-root", {
//   zoneId: zone.then(z => z.id),
//   name: "@",
//   type: "CNAME",
//   content: pagesProject.subdomain,
//   proxied: true,
// });
//
// const wwwRecord = new cloudflare.Record("autoarr-www", {
//   zoneId: zone.then(z => z.id),
//   name: "www",
//   type: "CNAME",
//   content: pagesProject.subdomain,
//   proxied: true,
// });

// =============================================================================
// Firebase / GCP Resources
// =============================================================================

// Enable required APIs
const firestoreApi = new gcp.projects.Service("firestore-api", {
  project: firebaseProjectId,
  service: "firestore.googleapis.com",
  disableOnDestroy: false,
});

const cloudFunctionsApi = new gcp.projects.Service("cloudfunctions-api", {
  project: firebaseProjectId,
  service: "cloudfunctions.googleapis.com",
  disableOnDestroy: false,
});

const cloudBuildApi = new gcp.projects.Service("cloudbuild-api", {
  project: firebaseProjectId,
  service: "cloudbuild.googleapis.com",
  disableOnDestroy: false,
});

// Firestore Database (Native mode)
const firestoreDb = new gcp.firestore.Database(
  "autoarr-interest-db",
  {
    project: firebaseProjectId,
    name: "(default)",
    locationId: "europe-west2", // London
    type: "FIRESTORE_NATIVE",
  },
  { dependsOn: [firestoreApi] }
);

// Firestore Security Rules
const firestoreRules = new gcp.firebaserules.Ruleset(
  "interest-form-rules",
  {
    project: firebaseProjectId,
    source: {
      files: [
        {
          name: "firestore.rules",
          content: `
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Interest submissions - write only from authenticated sources (Cloud Functions)
    match /interest_submissions/{submission} {
      allow read: if false; // Admin only via console/SDK
      allow write: if false; // Only via Cloud Function
    }

    // Analytics aggregates - read only
    match /analytics/{doc} {
      allow read: if false; // Admin only
      allow write: if false;
    }
  }
}
`,
        },
      ],
    },
  },
  { dependsOn: [firestoreDb] }
);

// Cloud Storage bucket for Cloud Functions source
const functionsBucket = new gcp.storage.Bucket("autoarr-functions-source", {
  project: firebaseProjectId,
  name: `${firebaseProjectId}-functions-source`,
  location: "EUROPE-WEST2",
  uniformBucketLevelAccess: true,
  forceDestroy: true,
});

// =============================================================================
// Outputs
// =============================================================================

export const turnstileSiteKey = turnstileWidget.id;
export const turnstileSecretKey = turnstileWidget.secret;
export const pagesUrl = pagesProject.subdomain.apply((s) => `https://${s}`);
export const pagesProjectName = pagesProject.name;
export const firebaseProject = firebaseProjectId;
export const functionsBucketName = functionsBucket.name;

// Export for use in site build
export const siteConfig = pulumi.all([turnstileWidget.id, firebaseProjectId]).apply(
  ([siteKey, projectId]) =>
    JSON.stringify({
      turnstileSiteKey: siteKey,
      firebaseProjectId: projectId,
    })
);
