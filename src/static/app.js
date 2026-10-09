function animateEvidenceBars() {
    const bars = document.querySelectorAll(".evidence-fill");

    // Reset every bar first
    bars.forEach(bar => {
        bar.style.width = "0%";
    });
    
    // Wait until the browser has rendered the initial zero-width state
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            // Set percentage widths for bearing-evidence visualization    
            bars.forEach(bar => {
                const width = Number(bar.dataset.width);

                // Apply inline CSS style (style="width: __%;")
                if (Number.isFinite(width)) {
                    bar.style.width = `${width}%`;
                }
            });
        });
    });
}

// Runs on initial load and back/forward navigation (bfcache)
window.addEventListener("pageshow", animateEvidenceBars);
