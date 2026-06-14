(() => {
  let target = null;
  let lastX = 0;
  let lastY = 0;
  let dragging = false;
  let pointerActive = false;
  let suppressClick = false;
  let mouseActive = false;
  let startElement = null;
  let markedVideoPlayers = [];

  const largestScroller = (axis) => {
    const documentScroller = document.scrollingElement || document.documentElement;
    const options = descendants(document, axis);
    if (canScroll(documentScroller, axis)) options.push(documentScroller);
    return options.sort((a, b) => {
      const aRoom = axis === "vertical" ? a.scrollHeight - a.clientHeight : a.scrollWidth - a.clientWidth;
      const bRoom = axis === "vertical" ? b.scrollHeight - b.clientHeight : b.scrollWidth - b.clientWidth;
      return bRoom - aRoom;
    })[0] || documentScroller;
  };

  const addGestureLayer = () => {
    if (window !== window.top || !document.body || document.querySelector("#pi-tablet-gesture-layer")) return;
    const layer = document.createElement("div");
    layer.id = "pi-tablet-gesture-layer";
    let downX = 0;
    let downY = 0;
    let lastLayerX = 0;
    let lastLayerY = 0;
    let moved = false;
    let active = false;
    let layerTarget = null;

    const underlying = (x, y) => {
      layer.style.pointerEvents = "none";
      const element = document.elementFromPoint(x, y);
      layer.style.pointerEvents = "auto";
      return element;
    };

    const start = (event) => {
      if (!event.isPrimary || (event.pointerType === "mouse" && event.button !== 0)) return;
      active = true;
      moved = false;
      downX = lastLayerX = event.clientX;
      downY = lastLayerY = event.clientY;
      layerTarget = underlying(event.clientX, event.clientY);
      layer.setPointerCapture?.(event.pointerId);
      event.preventDefault();
    };

    const drag = (event) => {
      if (!active || !event.isPrimary) return;
      const dx = lastLayerX - event.clientX;
      const dy = lastLayerY - event.clientY;
      if (Math.abs(event.clientX - downX) + Math.abs(event.clientY - downY) > 6) moved = true;
      if (moved) {
        const axis = Math.abs(dy) >= Math.abs(dx) ? "vertical" : "horizontal";
        const scroller = largestScroller(axis);
        if (axis === "vertical") scroller.scrollTop += dy;
        else scroller.scrollLeft += dx;
        layerTarget?.dispatchEvent(new WheelEvent("wheel", {
          bubbles: true,
          cancelable: true,
          deltaX: axis === "horizontal" ? dx : 0,
          deltaY: axis === "vertical" ? dy : 0
        }));
      }
      lastLayerX = event.clientX;
      lastLayerY = event.clientY;
      event.preventDefault();
    };

    const end = (event) => {
      if (!active) return;
      active = false;
      layer.releasePointerCapture?.(event.pointerId);
      if (!moved) underlying(event.clientX, event.clientY)?.click();
      event.preventDefault();
    };

    layer.addEventListener("pointerdown", start, { passive: false });
    layer.addEventListener("pointermove", drag, { passive: false });
    layer.addEventListener("pointerup", end, { passive: false });
    layer.addEventListener("pointercancel", () => { active = false; }, { passive: false });
    document.body.append(layer);
  };

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

  const canScroll = (element, axis = "both") => {
    if (!element) return false;
    const vertical = element.scrollHeight > element.clientHeight + 2;
    const horizontal = element.scrollWidth > element.clientWidth + 2;
    return axis === "vertical" ? vertical : axis === "horizontal" ? horizontal : vertical || horizontal;
  };

  const descendants = (root, axis, found = []) => {
    for (const element of root.querySelectorAll?.("*") || []) {
      if (canScroll(element, axis)) found.push(element);
      if (element.shadowRoot) descendants(element.shadowRoot, axis, found);
    }
    return found;
  };

  const scrollable = (start, axis) => {
    let element = start instanceof Element ? start : document.documentElement;
    while (element && element !== document.documentElement) {
      if (canScroll(element, axis)) return element;
      element = element.parentElement;
    }
    const documentScroller = document.scrollingElement || document.documentElement;
    if (canScroll(documentScroller, axis)) return documentScroller;
    return descendants(document, axis)
      .sort((a, b) =>
        (b.scrollHeight - b.clientHeight + b.scrollWidth - b.clientWidth) -
        (a.scrollHeight - a.clientHeight + a.scrollWidth - a.clientWidth)
      )[0] || documentScroller;
  };

  const begin = (x, y, element) => {
    target = null;
    startElement = element;
    lastX = x;
    lastY = y;
    dragging = false;
    suppressClick = false;
  };

  const move = (event, x, y) => {
    const dx = lastX - x;
    const dy = lastY - y;
    if (Math.abs(dx) + Math.abs(dy) > 5) dragging = true;
    if (dragging) {
      if (!target) {
        target = scrollable(startElement, Math.abs(dy) >= Math.abs(dx) ? "vertical" : "horizontal");
      }
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
    if (event.target?.id === "pi-tablet-gesture-layer") return;
    if (!event.isPrimary || (event.button !== 0 && event.pointerType === "mouse")) return;
    pointerActive = true;
    begin(event.clientX, event.clientY, event.target);
    event.target?.setPointerCapture?.(event.pointerId);
  }, { capture: true, passive: false });

  addEventListener("pointermove", (event) => {
    if (event.target?.id === "pi-tablet-gesture-layer") return;
    if (pointerActive && event.isPrimary) move(event, event.clientX, event.clientY);
  }, { capture: true, passive: false });

  addEventListener("pointerup", (event) => {
    pointerActive = false;
    event.target?.releasePointerCapture?.(event.pointerId);
    target = null;
    startElement = null;
  }, { capture: true, passive: false });

  addEventListener("pointercancel", () => {
    pointerActive = false;
    target = null;
    startElement = null;
  }, { capture: true });

  addEventListener("mousedown", (event) => {
    if (event.target?.id === "pi-tablet-gesture-layer") return;
    if (event.button !== 0) return;
    mouseActive = true;
    begin(event.clientX, event.clientY, event.target);
    if (event.cancelable) event.preventDefault();
  }, { capture: true, passive: false });

  addEventListener("mousemove", (event) => {
    if (event.target?.id === "pi-tablet-gesture-layer") return;
    if (mouseActive && (event.buttons & 1) === 1) {
      move(event, event.clientX, event.clientY);
    }
  }, { capture: true, passive: false });

  addEventListener("mouseup", () => {
    mouseActive = false;
    target = null;
    startElement = null;
  }, { capture: true, passive: false });

  addEventListener("click", (event) => {
    if (suppressClick) {
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }
  }, { capture: true });

  const parentAcrossRoots = (element) => {
    if (element?.parentElement) return element.parentElement;
    const root = element?.getRootNode?.();
    return root instanceof ShadowRoot ? root.host : null;
  };

  const videosIn = (root, found = []) => {
    for (const element of root.querySelectorAll?.("*") || []) {
      if (element instanceof HTMLVideoElement) found.push(element);
      if (element.shadowRoot) videosIn(element.shadowRoot, found);
    }
    return found;
  };

  const markVideoPlayer = (video) => {
    let element = parentAcrossRoots(video);
    let player = null;

    while (element && element !== document.body && element !== document.documentElement) {
      const rect = element.getBoundingClientRect();
      if (rect.width >= innerWidth * 0.8 && rect.height >= innerHeight * 0.55) {
        player = element;
      }
      element = parentAcrossRoots(element);
    }

    if (player) {
      player.setAttribute("data-pi-video-player", "true");
      markedVideoPlayers.push(player);
    }
  };

  const updateVideoMode = () => {
    if (window === window.top) document.body?.classList.add("pi-tablet-top");
    addGestureLayer();
    addNavigation();
    markedVideoPlayers.forEach((element) => {
      element.removeAttribute("data-pi-video-player");
    });
    markedVideoPlayers = [];
    const visibleVideos = videosIn(document).filter((video) => {
      const rect = video.getBoundingClientRect();
      const style = getComputedStyle(video);
      return (
        rect.width > 200 &&
        rect.height > 120 &&
        rect.bottom > 0 &&
        rect.top < innerHeight &&
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        Number(style.opacity) > 0
      );
    });
    visibleVideos.forEach(markVideoPlayer);
    const playing = visibleVideos.length > 0;
    document.body?.classList.toggle("pi-video-playing", playing);
  };

  new MutationObserver(updateVideoMode).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
  addEventListener("play", updateVideoMode, true);
  addEventListener("pause", updateVideoMode, true);
  addEventListener("popstate", updateVideoMode);
  addEventListener("hashchange", updateVideoMode);
  addEventListener("DOMContentLoaded", updateVideoMode, { once: true });
  setInterval(updateVideoMode, 500);
})();
