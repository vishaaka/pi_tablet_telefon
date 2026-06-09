(() => {
  let target = null;
  let lastX = 0;
  let lastY = 0;
  let dragging = false;

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
  };

  const move = (event, x, y) => {
    if (!target) return;
    const dx = lastX - x;
    const dy = lastY - y;
    if (Math.abs(dx) + Math.abs(dy) > 4) dragging = true;
    if (dragging) {
      target.scrollBy({ left: dx, top: dy, behavior: "auto" });
      event.preventDefault();
    }
    lastX = x;
    lastY = y;
  };

  addEventListener("touchstart", (event) => {
    const touch = event.touches[0];
    if (touch) begin(touch.clientX, touch.clientY, event.target);
  }, { capture: true, passive: false });

  addEventListener("touchmove", (event) => {
    const touch = event.touches[0];
    if (touch) move(event, touch.clientX, touch.clientY);
  }, { capture: true, passive: false });

  addEventListener("touchend", () => {
    target = null;
  }, { capture: true });

  addEventListener("pointerdown", (event) => {
    if (!("ontouchstart" in window) && event.pointerType === "touch") {
      begin(event.clientX, event.clientY, event.target);
    }
  }, { capture: true });

  addEventListener("pointermove", (event) => {
    if (!("ontouchstart" in window) && event.pointerType === "touch") {
      move(event, event.clientX, event.clientY);
    }
  }, { capture: true });

  addEventListener("pointerup", () => {
    target = null;
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
