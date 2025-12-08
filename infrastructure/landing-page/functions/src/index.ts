import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

// Initialize Firebase Admin
admin.initializeApp();

const db = admin.firestore();

// Interest level mapping for analytics
const INTEREST_LEVELS = {
  excited: 3,
  curious: 2,
  informed: 1,
} as const;

type InterestLevel = keyof typeof INTEREST_LEVELS;

interface InterestSubmission {
  email: string;
  interest: InterestLevel;
  services: string[];
  turnstileToken: string;
  timestamp: string;
  userAgent: string;
  referrer: string;
}

interface TurnstileResponse {
  success: boolean;
  "error-codes"?: string[];
  challenge_ts?: string;
  hostname?: string;
}

/**
 * Verify Cloudflare Turnstile token
 */
async function verifyTurnstile(token: string): Promise<boolean> {
  const secretKey = process.env.TURNSTILE_SECRET_KEY;

  if (!secretKey) {
    functions.logger.error("TURNSTILE_SECRET_KEY not configured");
    return false;
  }

  try {
    const response = await fetch(
      "https://challenges.cloudflare.com/turnstile/v0/siteverify",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          secret: secretKey,
          response: token,
        }),
      }
    );

    const data = (await response.json()) as TurnstileResponse;

    if (!data.success) {
      functions.logger.warn("Turnstile verification failed:", data["error-codes"]);
    }

    return data.success;
  } catch (error) {
    functions.logger.error("Turnstile verification error:", error);
    return false;
  }
}

/**
 * Validate email format
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Main function to handle interest form submissions
 */
export const submitInterest = functions
  .region("europe-west2") // London region for GDPR compliance
  .runWith({
    maxInstances: 10,
    memory: "256MB",
  })
  .https.onRequest(async (req, res) => {
    // CORS headers
    res.set("Access-Control-Allow-Origin", "*");
    res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.set("Access-Control-Allow-Headers", "Content-Type");

    // Handle preflight
    if (req.method === "OPTIONS") {
      res.status(204).send("");
      return;
    }

    // Only allow POST
    if (req.method !== "POST") {
      res.status(405).json({ success: false, error: "Method not allowed" });
      return;
    }

    try {
      const body = req.body as InterestSubmission;

      // Validate required fields
      if (!body.email || !body.interest || !body.turnstileToken) {
        res.status(400).json({
          success: false,
          error: "Missing required fields",
        });
        return;
      }

      // Validate email format
      if (!isValidEmail(body.email)) {
        res.status(400).json({
          success: false,
          error: "Invalid email format",
        });
        return;
      }

      // Validate interest level
      if (!["excited", "curious", "informed"].includes(body.interest)) {
        res.status(400).json({
          success: false,
          error: "Invalid interest level",
        });
        return;
      }

      // Verify Turnstile token
      const turnstileValid = await verifyTurnstile(body.turnstileToken);
      if (!turnstileValid) {
        res.status(403).json({
          success: false,
          error: "Security verification failed. Please try again.",
        });
        return;
      }

      // Check for duplicate email (within last 24 hours to prevent spam)
      const recentSubmission = await db
        .collection("interest_submissions")
        .where("email", "==", body.email.toLowerCase())
        .where("createdAt", ">", admin.firestore.Timestamp.fromDate(
          new Date(Date.now() - 24 * 60 * 60 * 1000)
        ))
        .limit(1)
        .get();

      if (!recentSubmission.empty) {
        // Update existing submission instead of creating duplicate
        const existingDoc = recentSubmission.docs[0];
        await existingDoc.ref.update({
          interest: body.interest,
          services: body.services || [],
          updatedAt: admin.firestore.FieldValue.serverTimestamp(),
          updateCount: admin.firestore.FieldValue.increment(1),
        });

        functions.logger.info(`Updated interest submission for ${body.email}`);

        res.status(200).json({
          success: true,
          message: "Preferences updated",
        });
        return;
      }

      // Create new submission
      const submission = {
        email: body.email.toLowerCase(),
        interest: body.interest,
        interestScore: INTEREST_LEVELS[body.interest],
        services: body.services || [],
        referrer: body.referrer || "direct",
        userAgent: body.userAgent || "unknown",
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        updatedAt: admin.firestore.FieldValue.serverTimestamp(),
        updateCount: 0,
        // GDPR: Don't store IP addresses
      };

      await db.collection("interest_submissions").add(submission);

      // Update analytics counters
      const analyticsRef = db.collection("analytics").doc("interest_totals");
      await analyticsRef.set(
        {
          total: admin.firestore.FieldValue.increment(1),
          [`by_interest.${body.interest}`]: admin.firestore.FieldValue.increment(1),
          lastUpdated: admin.firestore.FieldValue.serverTimestamp(),
        },
        { merge: true }
      );

      // Update service popularity
      if (body.services && body.services.length > 0) {
        const servicesRef = db.collection("analytics").doc("service_popularity");
        const serviceUpdates: Record<string, FirebaseFirestore.FieldValue> = {
          lastUpdated: admin.firestore.FieldValue.serverTimestamp(),
        };
        body.services.forEach((service) => {
          serviceUpdates[service] = admin.firestore.FieldValue.increment(1);
        });
        await servicesRef.set(serviceUpdates, { merge: true });
      }

      functions.logger.info(`New interest submission from ${body.email}`, {
        interest: body.interest,
        services: body.services,
      });

      res.status(200).json({
        success: true,
        message: "Thank you for your interest!",
      });
    } catch (error) {
      functions.logger.error("Error processing submission:", error);
      res.status(500).json({
        success: false,
        error: "An error occurred. Please try again.",
      });
    }
  });

/**
 * Scheduled function to generate daily analytics summary
 */
export const dailyAnalyticsSummary = functions
  .region("europe-west2")
  .pubsub.schedule("0 9 * * *") // 9 AM UTC daily
  .timeZone("Europe/London")
  .onRun(async () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(0, 0, 0, 0);

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const submissions = await db
      .collection("interest_submissions")
      .where("createdAt", ">=", admin.firestore.Timestamp.fromDate(yesterday))
      .where("createdAt", "<", admin.firestore.Timestamp.fromDate(today))
      .get();

    const summary = {
      date: yesterday.toISOString().split("T")[0],
      totalSubmissions: submissions.size,
      byInterest: {
        excited: 0,
        curious: 0,
        informed: 0,
      },
      services: {} as Record<string, number>,
    };

    submissions.forEach((doc) => {
      const data = doc.data();
      summary.byInterest[data.interest as InterestLevel]++;
      (data.services || []).forEach((service: string) => {
        summary.services[service] = (summary.services[service] || 0) + 1;
      });
    });

    await db.collection("analytics").doc(`daily_${summary.date}`).set(summary);

    functions.logger.info("Daily analytics summary generated:", summary);
  });
