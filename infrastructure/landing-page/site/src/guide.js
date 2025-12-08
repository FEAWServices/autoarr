// Guide page interactivity

document.addEventListener("DOMContentLoaded", function () {
  // Accordion functionality
  const accordionHeaders = document.querySelectorAll(".accordion-header");

  accordionHeaders.forEach(function (header) {
    header.addEventListener("click", function () {
      const item = this.parentElement;
      const isActive = item.classList.contains("active");

      // Close all other items
      document.querySelectorAll(".accordion-item").forEach(function (i) {
        i.classList.remove("active");
      });

      // Toggle current item
      if (!isActive) {
        item.classList.add("active");
      }
    });
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href");
      if (targetId === "#") return;

      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });

        // Update URL without jumping
        history.pushState(null, null, targetId);
      }
    });
  });

  // Highlight active nav link on scroll
  const sections = document.querySelectorAll(".guide-section[id]");
  const navLinks = document.querySelectorAll(".guide-nav-link");

  function highlightNavLink() {
    const scrollPos = window.scrollY + 200;

    sections.forEach(function (section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute("id");

      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach(function (link) {
          link.classList.remove("active");
          if (link.getAttribute("href") === "#" + id) {
            link.classList.add("active");
          }
        });
      }
    });
  }

  window.addEventListener("scroll", highlightNavLink);
  highlightNavLink();

  // Copy code blocks on click
  document.querySelectorAll(".code-block").forEach(function (block) {
    block.style.cursor = "pointer";
    block.title = "Click to copy";

    block.addEventListener("click", function () {
      const code = this.querySelector("code").textContent;
      navigator.clipboard.writeText(code).then(function () {
        // Show feedback
        const originalBg = block.style.borderColor;
        block.style.borderColor = "var(--color-success)";
        setTimeout(function () {
          block.style.borderColor = originalBg;
        }, 500);
      });
    });
  });
});
