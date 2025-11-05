/* Dynamically resize iframes with Nova Act HTML logs when accordions are expanded */

document.addEventListener('change', function(e) {
  // Listen to change events on our accordion toggle elements
  if (e.target.type === 'checkbox' && e.target.checked && e.target.id.startsWith('accordion-toggle')) {
    // Get the iframe with the embedded Nova Act HTML logs
    const iframe = e.target.parentElement.querySelector('iframe');
    if (!iframe || iframe.dataset.resized) return;
    
    // Calculate and set iframe height once
    function resizeIframe() {
      if (iframe.dataset.resized) return;
      // Wait for DOM to settle
      requestAnimationFrame(function() {
        try {
          const doc = iframe.contentDocument;
          const body = doc.body;
          // Temporarily remove overflow and height constraints to calculate true content height
          const originalOverflow = body.style.overflow;
          const originalMaxHeight = body.style.maxHeight;
          body.style.overflow = 'visible';
          body.style.maxHeight = 'none';
          const height = Math.max(body.scrollHeight, doc.documentElement.scrollHeight);
          // Restore original styles
          body.style.overflow = originalOverflow;
          body.style.maxHeight = originalMaxHeight;
          // Set iframe height to match content
          iframe.style.height = height + 'px';
          iframe.dataset.resized = 'true';
        } catch (e) {
          // If we can't calculate the iframe height, fallback to a default height
          console.error('Error resizing iframe:', e);
          iframe.style.height = '600px';
        }
      });
    }
    
    // Resize immediately if iframe already loaded, otherwise wait for load event
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      resizeIframe();
    } else {
      iframe.addEventListener('load', resizeIframe, { once: true });
    }
  }
});
