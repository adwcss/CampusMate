"use strict";
const selectedSchoolId = "hnvust";
const schoolPageUrl = new URL(location.href);
if (schoolPageUrl.searchParams.has("school_id") && schoolPageUrl.searchParams.get("school_id") !== selectedSchoolId) {
  schoolPageUrl.searchParams.set("school_id", selectedSchoolId);
  history.replaceState(null, "", schoolPageUrl);
}

function schoolFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (String(path).startsWith("/api/")) headers.set("X-CampusMate-School", selectedSchoolId);
  return window.fetch(path, {...options, headers});
}

async function initializeSchool() {
  const data = await api("/api/schools");
  const school = data.schools.find(row => row.school_id === selectedSchoolId);
  if (!school) throw new Error("学校配置不存在，请返回首页选择学校。");
  state.school = school;
  document.querySelector(".brand strong").textContent = "CampusMate";
  document.querySelector(".brand small").textContent = school.short_name + " · 新生助手";
  document.querySelector(".intro-school").textContent = school.name;
  document.querySelector("#school-status").textContent = school.status;
  document.querySelector("#map-notice").textContent = school.map_notice;
  if (school.official_map) {
    const link = element("a", "secondary", "查看学校官网校园地图");
    link.href = school.official_map;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    document.querySelector("#map-notice").append(document.createTextNode(" "), link);
  }
  const home = document.querySelector("#school-home");
  home.hidden = !school.official_home;
  if (school.official_home) home.href = school.official_home;
  document.querySelectorAll("img[data-campus-map]").forEach(image => {
    image.src = school.map_image || "/campus-map.svg?school_id=" + encodeURIComponent(selectedSchoolId);
    image.alt = school.map_notice;
    image.width = school.map_width || 928;
    image.height = school.map_height || 1120;
  });
  initializeMapPresentation(school);
  document.body.classList.toggle("school-template", !school.legacy_content);
  if (!school.legacy_content) {
    document.querySelectorAll("nav a[data-view]").forEach(link => {
      link.hidden = !["chat", "tasks", "map", "sources", "checklist"].includes(link.dataset.view);
    });
    document.querySelector(".contact-note").hidden = true;
    document.querySelector(".campus3d-entry").hidden = true;
    const intro = document.querySelector("#intro-dialog"); if (intro.open) intro.close();
  }
  initializeArrivalGenerator();
}

function initializeMapPresentation(school) {
  const toolbar = document.querySelector(".map-toolbar>div");
  const show = element("label", "map-marker-toggle");
  const checkbox = element("input"); checkbox.type = "checkbox"; checkbox.id = "show-map-markers";
  show.append(checkbox, document.createTextNode("显示地点标记"));
  checkbox.addEventListener("change", () => { state.showMapMarkers = checkbox.checked; renderPlaces(); });
  toolbar.prepend(show);
  const compare = document.querySelector("#map-image-version");
  compare.hidden = !school.map_original;
  let original = false;
  compare.addEventListener("click", () => {
    original = !original;
    document.querySelectorAll("img[data-campus-map]").forEach(image => {
      image.src = original ? school.map_original : school.map_image;
      image.width = original ? (school.map_original_width || 813) : school.map_width;
      image.height = original ? (school.map_original_height || 792) : school.map_height;
    });
    state.originalMap = original;
    compare.textContent = original ? "返回美化地图" : "对照上传原图";
    compare.setAttribute("aria-pressed", String(original));
    document.querySelector("#map-dialog-title").textContent = original ? "用户上传原图" : "美化地图 · 图中文字请对照原图";
    if (orientationReady) renderItinerary();
    renderPlaces();
  });
}

function initializeArrivalGenerator() {
  const form = document.querySelector("#arrival-personalize");
  let previewProfile = null;
  form.addEventListener("input", () => { previewProfile = null; document.querySelector("#arrival-apply").disabled = true; });
  const profile = () => ({arrival_date: form.elements.arrival_date.value,
    live_on_campus: form.elements.live_on_campus.checked, need_aid: form.elements.need_aid.checked,
    long_distance: form.elements.long_distance.checked});
  form.addEventListener("submit", async event => {
    event.preventDefault();
    try {
      const candidate = profile();
      const result = await mutate("/api/arrival/preview", {profile: candidate});
      previewProfile = candidate;
      const list = document.querySelector("#arrival-preview");
      list.replaceChildren(...result.tasks.map(task => element("li", "", task.title + (task.due ? " · " + task.due : " · 未排期"))));
      document.querySelector("#arrival-apply").disabled = false;
      document.querySelector("#arrival-generator-status").textContent = result.note;
    } catch (error) { toast(error.message); }
  });
  document.querySelector("#arrival-apply").addEventListener("click", async () => {
    if (!previewProfile) return;
    const apply = document.querySelector("#arrival-apply"); apply.disabled = true;
    try {
      const result = await mutate("/api/arrival/generate", {profile: previewProfile});
      personalTasks = result.tasks; renderPlanner();
      document.querySelector("#arrival-generator-status").textContent = `已新增 ${result.added} 项，跳过 ${result.skipped} 项已生成建议；保留已有进度。`;
      previewProfile = null;
    } catch (error) { toast(error.message); apply.disabled = false; }
  });
}

function renderSearchMode(stats) {
  const hint = document.querySelector("#retrieval-hint");
  if (!state.school.legacy_content) {
    const select = document.querySelector("#retrieval-mode");
    select.replaceChildren(new Option("自动查询学校官网", "enhanced"));
    hint.textContent = stats.search_enabled ? "按问题查询本校公开网页，找到相关正文后附来源。" : "可通过查询链接查找本校公开通知。";
    return;
  }
  const select = document.querySelector("#retrieval-mode");
  select.options[0].textContent = stats.deepseek_search_enabled ? "自动检索（本地优先）" : "本地知识库";
  hint.textContent = stats.deepseek_search_enabled
    ? "默认优先查本地，资料不足时发送当前问题到 DeepSeek 检索公开资料，并附出处。请勿输入个人敏感信息。"
    : stats.search_enabled ? "可选择联网增强，查阅本地资料与学校官网。" : "当前使用本地资料。";
}

async function showOfficialMap(school) {
  if (document.querySelector("#official-map-preview")) return;
  const notice = document.querySelector("#map-notice");
  const preview = element("section", "official-map-preview");
  preview.id = "official-map-preview";
  notice.after(preview);
  for (const selector of [".map-layout", ".map-search-controls"])
    document.querySelector("#view-map " + selector).hidden = true;
  if (!school.official_map_asset) {
    notice.firstChild.textContent = school.official_map ? "请打开官网地图原件。" : "可通过学校官网查找校园地图。";
    return;
  }
  notice.firstChild.textContent = "下方展示学校官网公布的地图，校区与更新日期请查看原件。";
  const status = element("p", "", "正在加载官网地图…");
  preview.append(status);
  try {
    const response = await fetch("/api/official-map?school_id=" + encodeURIComponent(school.school_id));
    const kind = response.headers.get("Content-Type");
    if (!response.ok || !["application/pdf", "image/jpeg", "image/png"].includes(kind)) throw new Error("地图不可用");
    const isPdf = kind === "application/pdf";
    const media = document.createElement(isPdf ? "iframe" : "img");
    media.title = school.name + "官网校园地图";
    if (!isPdf) media.alt = media.title;
    const objectUrl = URL.createObjectURL(await response.blob());
    media.src = objectUrl;
    window.addEventListener("pagehide", () => URL.revokeObjectURL(objectUrl), {once: true});
    status.replaceWith(media);
  } catch {
    status.textContent = "地图预览加载失败，请打开官网原件。";
  }
}

async function bootTemplate() {
  const [stats, catalog, history, checklist, sources] = await Promise.all([
    api("/api/stats"), api("/api/catalog"), api(`/api/history?session=${state.session}`),
    api(`/api/checklist?session=${state.session}`), api("/api/sources")]);
  state.catalog = catalog; state.messages = history.messages; state.checked = checklist.checked;
  state.sources = sources.documents; state.explore = {items: []}; state.saved = [];
  await initializePlanner();
  document.querySelector("#knowledge-meta").textContent = "学校官网查询";
  document.querySelector("#mode-label").textContent = "官网联网查询";
  document.querySelector("#mode-detail").textContent = "提问时查询本校公开网页，回答附出处。";
  const category = document.querySelector("#map-category");
  ["", ...new Set(catalog.places.map(place => place.category))].forEach(value => { const option = element("option", "", value || "所有区域"); option.value = value; category.append(option); });
  category.addEventListener("change", event => { state.mapCategory = event.target.value; renderPlaces(); });
  document.querySelector("#map-search").addEventListener("input", event => { state.mapQuery = event.target.value.trim(); renderPlaces(); });
  renderSearchMode(stats);
  renderFaq(); renderMessages(); renderTasks(); renderPlaces(); renderSources();
  changeView(new URLSearchParams(location.search).get("view") || "chat", false);
}
