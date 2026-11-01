"use strict";
let selectedSchoolId = new URLSearchParams(location.search).get("school_id") || "hnvust";
// A page owns its school selection; another tab cannot silently retarget requests.
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
  const select = document.querySelector("#school-select");
  select.replaceChildren(...data.schools.map(row => {
    const option = element("option", "", row.name); option.value = row.school_id; return option;
  }));
  select.value = selectedSchoolId;
  select.addEventListener("change", () => {
    if (state.busy) { select.value = selectedSchoolId; toast("请等待当前回答完成再切换学校。"); return; }
    const url = new URL(location.href); url.searchParams.set("school_id", select.value);
    url.searchParams.set("view", "chat"); location.assign(url);
  });
  document.querySelector(".brand strong").textContent = "CampusMate";
  document.querySelector(".brand small").textContent = school.short_name + " · 新生助手";
  document.querySelector(".intro-school").textContent = school.name;
  document.querySelector("#school-status").textContent = school.status;
  document.querySelector("#map-notice").textContent = school.map_notice;
  const home = document.querySelector("#school-home");
  home.hidden = !school.official_home;
  if (school.official_home) home.href = school.official_home;
  document.querySelectorAll("img[data-campus-map]").forEach(image => {
    image.src = "/campus-map.svg?school_id=" + encodeURIComponent(selectedSchoolId);
    image.alt = school.map_notice;
  });
  document.body.classList.toggle("school-template", !school.legacy_content);
  if (!school.legacy_content) {
    document.querySelectorAll("nav a[data-view]").forEach(link => {
      link.hidden = !["chat", "tasks", "map", "sources", "checklist"].includes(link.dataset.view);
    });
    document.querySelector(".contact-note").hidden = true;
    const intro = document.querySelector("#intro-dialog"); if (intro.open) intro.close();
  }
  initializeArrivalGenerator();
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

async function bootTemplate() {
  const [stats, catalog, history, checklist, sources] = await Promise.all([
    api("/api/stats"), api("/api/catalog"), api(`/api/history?session=${state.session}`),
    api(`/api/checklist?session=${state.session}`), api("/api/sources")]);
  state.catalog = catalog; state.messages = history.messages; state.checked = checklist.checked;
  state.sources = sources.documents; state.explore = {items: []}; state.saved = [];
  await initializePlanner();
  document.querySelector("#knowledge-meta").textContent = `${stats.document_count} 份资料 · 待接入`;
  document.querySelector("#mode-label").textContent = "本地资料模式";
  document.querySelector("#mode-detail").textContent = "本校知识文件待补充；不会引用其他学校资料。";
  const category = document.querySelector("#map-category");
  ["", ...new Set(catalog.places.map(place => place.category))].forEach(value => { const option = element("option", "", value || "所有区域"); option.value = value; category.append(option); });
  category.addEventListener("change", event => { state.mapCategory = event.target.value; renderPlaces(); });
  document.querySelector("#map-search").addEventListener("input", event => { state.mapQuery = event.target.value.trim(); renderPlaces(); });
  renderFaq(); renderMessages(); renderTasks(); renderPlaces(); renderSources();
  changeView(new URLSearchParams(location.search).get("view") || "chat", false);
}
