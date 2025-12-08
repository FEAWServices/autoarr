// AutoArr Landing Page - Form Handler

// Configuration (injected at build time or via environment)
const CONFIG = {
  // These will be replaced by Cloudflare Pages environment variables
  turnstileSiteKey:
    window.TURNSTILE_SITE_KEY || "TURNSTILE_SITE_KEY_PLACEHOLDER",
  apiEndpoint:
    window.API_ENDPOINT ||
    "https://us-central1-YOUR_PROJECT.cloudfunctions.net/submitInterest",
};

// Turnstile token storage
let turnstileToken = null;

// Callback when Turnstile verification succeeds
window.onTurnstileSuccess = function (token) {
  turnstileToken = token;
  // Enable submit button
  const submitBtn = document.querySelector(
    "#interest-form button[type=submit]",
  );
  if (submitBtn) {
    submitBtn.disabled = false;
  }
};

// Form submission handler
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("interest-form");
  const messageEl = document.getElementById("form-message");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(form);
    const email = formData.get("email");
    const interest = formData.get("interest");
    const services = formData.getAll("services");

    // Validate
    if (!email || !interest) {
      showMessage("Please fill in all required fields.", "error");
      return;
    }

    if (!turnstileToken) {
      showMessage("Please complete the security verification.", "error");
      return;
    }

    // Show loading state
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.classList.add("loading");
    submitBtn.disabled = true;

    try {
      const response = await fetch(CONFIG.apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          interest,
          services,
          turnstileToken,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          referrer: document.referrer || "direct",
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        showMessage(getSuccessMessage(interest), "success");
        form.reset();
        // Reset Turnstile
        if (window.turnstile) {
          turnstile.reset();
        }
        turnstileToken = null;
      } else {
        throw new Error(data.error || "Submission failed");
      }
    } catch (error) {
      console.error("Form submission error:", error);
      showMessage("Something went wrong. Please try again later.", "error");
    } finally {
      submitBtn.classList.remove("loading");
      // Button stays disabled until Turnstile is completed again
    }
  });

  function showMessage(message, type) {
    messageEl.textContent = message;
    messageEl.className = `form-message ${type}`;
  }

  function getSuccessMessage(interest) {
    switch (interest) {
      case "excited":
        return "Awesome! We love your enthusiasm! You'll be first to know when AutoArr is ready. 🎉";
      case "curious":
        return "Thanks for your curiosity! We'll send you updates that help explain what AutoArr can do for you.";
      case "informed":
        return "Got it! We'll keep you in the loop with occasional updates. No spam, promise!";
      default:
        return "Thanks for your interest! We'll be in touch.";
    }
  }
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// Add intersection observer for scroll animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
    }
  });
}, observerOptions);

// Observe feature cards for animation
document.querySelectorAll(".feature-card").forEach((card) => {
  observer.observe(card);
});
