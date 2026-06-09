(() => {
  let target = null;
  let lastX = 0;
  let lastY = 0;
  let dragging = false;
  let pointerActive = false;
  let suppressClick = false;

  const addNavigation = () => {
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

  const scrollable = (start) => {
    let element = start instanceof Element ? start : document.documentElement;
    while (element && element !== document.documentElement) {
      const style = getComputedStyle(element);
      if (
        element.scrollHeight > element.clientHeight + 2 &&
        style.overflowY !== "hidden"
      ) {
        return element;
      }
      element = element.parentElement;
    }
    return document.scrollingElement || document.documentElement;
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
      target.scrollLeft += dx;
      target.scrollTop += dy;
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

  addEventListener("click", (event) => {
    if (suppressClick) {
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }
  }, { capture: true });

  const updateVideoMode = () => {
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
