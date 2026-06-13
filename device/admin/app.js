const $ = (selector) => document.querySelector(selector);
const appsEl = $("#apps");
const template = $("#app-template");
const installedSelect = $("#installed-app-select");
let config = { title: "Pi Tablet", background: "#f7f7fa", apps: [] };
let installedApps = [];
const builtInApps = {
  phone: { title: "Telefon", subtitle: "AI kişileri ara", color: "#bfe8d2", icon: "☎" },
  "youtube-kids": { title: "YouTube Kids", subtitle: "Güvenli video", color: "#ffd1d1", icon: "▶" },
  gcompris: { title: "Eğitim", subtitle: "GCompris etkinlikleri", color: "#d4ddff", icon: "ABC" },
  tuxpaint: { title: "Çizim", subtitle: "Tux Paint", color: "#ffe3b5", icon: "✎" },
  settings: { title: "Ses", subtitle: "Ses ayarları", color: "#dce8ef", icon: "♪" },
};

const defaultBase = location.protocol === "file:" ? "http://192.168.1.22:8090" : location.origin;
$("#pi-address").value = localStorage.getItem("pi-tablet-address") || defaultBase;
const api = (path) => $("#pi-address").value.replace(/\/+$/, "") + path;
const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
const iconForAction = (action = "") => {
  if (builtInApps[action]) return builtInApps[action].icon;
  if (action.includes("chromium") || action.includes("firefox")) return "◎";
  if (action.includes("calculator") || action.includes("galculator")) return "=";
  if (action.includes("terminal")) return ">_";
  if (action.includes("paint") || action.includes("draw")) return "✎";
  if (action.includes("game")) return "✦";
  return "◆";
};

const preview = () => {
  config.title = $("#title").value;
  config.background = $("#background").value;
  $("#preview-title").textContent = config.title;
  $(".tablet-screen").style.background = config.background;
  $("#preview-apps").innerHTML = config.apps
    .map((app) => `<div class="tile"><div class="tile-icon" style="background:${app.color}">${escapeHtml(app.icon || iconForAction(app.action))}</div><strong>${escapeHtml(app.title)}</strong></div>`)
    .join("");
};

const render = () => {
  $("#title").value = config.title;
  $("#background").value = config.background;
  appsEl.innerHTML = "";
  config.apps.forEach((app, index) => {
    app.icon ||= iconForAction(app.action);
    const node = template.content.cloneNode(true);
    const article = node.querySelector("article");
    article.querySelectorAll("[data-key]").forEach((element) => {
      element.value = app[element.dataset.key];
      element.oninput = () => {
        app[element.dataset.key] = element.value;
        preview();
      };
    });
    article.querySelectorAll("[data-move]").forEach((button) => {
      button.onclick = () => {
        const target = index + Number(button.dataset.move);
        if (target >= 0 && target < config.apps.length) {
          [config.apps[index], config.apps[target]] = [config.apps[target], config.apps[index]];
          render();
        }
      };
    });
    article.querySelector("[data-remove]").onclick = () => {
      config.apps.splice(index, 1);
      render();
    };
    appsEl.append(node);
  });
  preview();
};

const loadInstalledApps = async () => {
  installedSelect.innerHTML = '<option value="">Uygulamalar yükleniyor...</option>';
  try {
    const response = await fetch(api("/api/installed-apps"));
    if (!response.ok) throw new Error();
    installedApps = await response.json();
    installedSelect.innerHTML = "";
    if (installedApps.length) {
      installedApps.forEach((app) => installedSelect.add(new Option(app.name, app.id)));
    } else {
      installedSelect.add(new Option("Uygulama bulunamadı", ""));
    }
  } catch {
    installedApps = [];
    installedSelect.innerHTML = '<option value="">Liste alınamadı</option>';
  }
};

$("#title").oninput = preview;
$("#background").oninput = preview;
$("#add-built-in").onclick = () => {
  const action = $("#built-in-select").value;
  if (config.apps.some((app) => app.action === action)) {
    $("#state").textContent = "Zaten menüde";
    return;
  }
  config.apps.push({ ...builtInApps[action], action });
  render();
};
$("#refresh-apps").onclick = loadInstalledApps;
$("#add-installed").onclick = () => {
  const selected = installedApps.find((app) => app.id === installedSelect.value);
  if (!selected) return;
  if (config.apps.some((app) => app.action === `desktop:${selected.id}`)) {
    $("#state").textContent = "Zaten menüde";
    return;
  }
  config.apps.push({
    title: selected.name,
    subtitle: selected.comment || "Pi uygulaması",
    color: "#dce8ef",
    action: `desktop:${selected.id}`,
    icon: iconForAction(`desktop:${selected.id}`),
  });
  render();
};

const connect = async () => {
  localStorage.setItem("pi-tablet-address", $("#pi-address").value);
  $("#state").textContent = "Bağlanıyor";
  try {
    const response = await fetch(api("/api/config"));
    if (!response.ok) throw new Error();
    config = await response.json();
    $("#state").textContent = "Bağlı";
    render();
    await loadInstalledApps();
  } catch {
    $("#state").textContent = "Bağlantı yok";
  }
};

$("#connect").onclick = connect;
$("#save").onclick = async () => {
  preview();
  $("#state").textContent = "Kaydediliyor";
  try {
    const response = await fetch(api("/api/config"), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    $("#state").textContent = response.ok ? "Uygulandı" : "Hata";
  } catch {
    $("#state").textContent = "Bağlantı yok";
  }
};

connect();
