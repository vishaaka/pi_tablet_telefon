(() => {
  let target = null;
  let lastX = 0;
  let lastY = 0;
  let dragging = false;
  let pointerActive = false;
  let suppressClick = false;
  let mouseActive = false;

  const addNavigation = () => {
    if (window !== window.top) return;
    if (!document.body || document.querySelector("#pi-tablet-navigation")) return;
    const navigation = document.createElement("nav");
    navigation.id = "pi-tablet-navigation";
    navigation.innerHTML = `
      <button type="button" aria-label="Geri">&#9665;</button>
      <button type="button" aria-label="YouTube Kids ana sayfa">&#9675;</button>
      <button type="button" aria-label="YouTube Kids kapat">&#9633;</button>
    `;
    const buttons = navigation.querySelectorAll("button");
    buttons[0].addEventListener("click", () => history.back());
    buttons[1].addEventListener("click", () => location.assign("https://www.youtubekids.com/"));
    buttons[2].addEventListener("click", () => {
      location.assign("http://127.0.0.1:8090/system/exit-youtube-kids");
    });
    document.body.append(navigation);
  };

  const canScroll = (element) =>
    element &&
    (
      element.scrollHeight > element.clientHeight + 2 ||
      element.scrollWidth > element.clientWidth + 2
    );

  const descendants = (root, found = []) => {
    for (const element of root.querySelectorAll?.("*") || []) {
      if (canScroll(element)) found.push(element);
      if (element.shadowRoot) descendants(element.shadowRoot, found);
    }
    return found;
  };

  const scrollable = (start) => {
    let element = start instanceof Element ? start : document.documentElement;
    while (element && element !== document.documentElement) {
      if (canScroll(element)) return element;
      element = element.parentElement;
    }
    const documentScroller = document.scrollingElement || document.documentElement;
    if (canScroll(documentScroller)) return documentScroller;
    return descendants(document)
      .sort((a, b) =>
        (b.scrollHeight - b.clientHeight + b.scrollWidth - b.clientWidth) -
        (a.scrollHeight - a.clientHeight + a.scrollWidth - a.clientWidth)
      )[0] || documentScroller;
  };

  const begin = (x, y, element) => {
    target = scrollable(element);
    lastX = x;
    lastY = y;
    dragging = false;
    suppressClick = false;
  };

  const move = (event, x, y) => {
    if (!target) return;
    const dx = lastX - x;
    const dy = lastY - y;
    if (Math.abs(dx) + Math.abs(dy) > 5) dragging = true;
    if (dragging) {
      suppressClick = true;
      const verticalRoom = target.scrollHeight - target.clientHeight;
      const horizontalRoom = target.scrollWidth - target.clientWidth;
      if (verticalRoom > 2) target.scrollTop += dy;
      if (horizontalRoom > 2 && (verticalRoom <= 2 || Math.abs(dx) > Math.abs(dy))) {
        target.scrollLeft += dx;
      }
      if (verticalRoom <= 2 && horizontalRoom <= 2) {
        window.scrollBy(dx, dy);
      }
      if (event.cancelable) event.preventDefault();
      event.stopPropagation();
    }
    lastX = x;
    lastY = y;
  };

  addEventListener("pointerdown", (event) => {
    if (!event.isPrimary || (event.button !== 0 && event.pointerType === "mouse")) return;
    pointerActive = true;
    begin(event.clientX, event.clientY, event.target);
    event.target?.setPointerCapture?.(event.pointerId);
  }, { capture: true, passive: false });

  addEventListener("pointermove", (event) => {
    if (pointerActive && event.isPrimary) move(event, event.clientX, event.clientY);
  }, { capture: true, passive: false });

  addEventListener("pointerup", (event) => {
    pointerActive = false;
    event.target?.releasePointerCapture?.(event.pointerId);
    target = null;
  }, { capture: true, passive: false });

  addEventListener("pointercancel", () => {
    pointerActive = false;
    target = null;
  }, { capture: true });

  addEventListener("mousedown", (event) => {
    if (event.button !== 0) return;
    mouseActive = true;
    begin(event.clientX, event.clientY, event.target);
    if (event.cancelable) event.preventDefault();
  }, { capture: true, passive: false });

  addEventListener("mousemove", (event) => {
    if (mouseActive && (event.buttons & 1) === 1) {
      move(event, event.clientX, event.clientY);
    }
  }, { capture: true, passive: false });

  addEventListener("mouseup", () => {
    mouseActive = false;
    target = null;
  }, { capture: true, passive: false });

  addEventListener("click", (event) => {
    if (suppressClick) {
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }
  }, { capture: true });

  const updateVideoMode = () => {
    if (window === window.top) document.body?.classList.add("pi-tablet-top");
    addNavigation();
    const playing = [...document.querySelectorAll("video")].some(
      (video) => !video.paused && !video.ended
    );
    document.body?.classList.toggle("pi-video-playing", playing);
  };

  new MutationObserver(updateVideoMode).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
  addEventListener("play", updateVideoMode, true);
  addEventListener("pause", updateVideoMode, true);
  addEventListener("DOMContentLoaded", updateVideoMode, { once: true });
})();
