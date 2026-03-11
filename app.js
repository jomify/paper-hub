const state = {
  config: {
    openaiEnabled: false,
    openaiModel: "",
    aiEnabled: false,
    aiModel: "",
    aiProvider: "openai",
    aiProviderLabel: "OpenAI",
    supportsVisionTranslation: false,
    providerPresets: []
  },
  providerConfig: null,
  papers: [],
  selectedPaperId: null,
  activeTag: "all",
  editingPaperId: null,
  draftCoverImage: "",
  digests: {},
  topicDiscovery: {
    payload: null
  },
  libraryMap: {
    payload: null,
    view: "mind",
    scope: "library",
    expandedThemes: new Set(),
    activeNodeId: "",
    hoveredNodeId: "",
    nodeIndex: new Map(),
    viewport: createLibraryMapViewport("mind")
  },
  reader: {
    paperId: null,
    pages: [],
    currentPage: 1,
    mode: "original",
    translations: {},
    loadingPages: new Set(),
    observer: null,
    saveTimer: null,
    translationJob: null,
    translationJobTimer: null,
    translationLoadedPages: 0
  },
  view: "grid",
  filters: {
    search: "",
    status: "all",
    collection: "all",
    favoritesOnly: false,
    sort: "recent"
  }
};

const statusText = {
  "to-read": "待读",
  reading: "在读",
  reviewing: "复读",
  completed: "已读"
};

const priorityText = {
  low: "低优先",
  medium: "中优先",
  high: "高优先"
};

const elements = {
  statGrid: document.querySelector("#statGrid"),
  appNotice: document.querySelector("#appNotice"),
  tagCloud: document.querySelector("#tagCloud"),
  readingStack: document.querySelector("#readingStack"),
  paperGrid: document.querySelector("#paperGrid"),
  resultMeta: document.querySelector("#resultMeta"),
  searchInput: document.querySelector("#searchInput"),
  statusFilter: document.querySelector("#statusFilter"),
  collectionFilter: document.querySelector("#collectionFilter"),
  favoriteFilter: document.querySelector("#favoriteFilter"),
  sortFilter: document.querySelector("#sortFilter"),
  newPaperButton: document.querySelector("#newPaperButton"),
  importButton: document.querySelector("#importButton"),
  topicDiscoveryButton: document.querySelector("#topicDiscoveryButton"),
  mapButton: document.querySelector("#mapButton"),
  providerSettingsButton: document.querySelector("#providerSettingsButton"),
  importInput: document.querySelector("#importInput"),
  exportButton: document.querySelector("#exportButton"),
  seedButton: document.querySelector("#seedButton"),
  gridViewButton: document.querySelector("#gridViewButton"),
  listViewButton: document.querySelector("#listViewButton"),
  paperDialog: document.querySelector("#paperDialog"),
  paperForm: document.querySelector("#paperForm"),
  dialogTitle: document.querySelector("#dialogTitle"),
  closeDialogButton: document.querySelector("#closeDialogButton"),
  cancelDialogButton: document.querySelector("#cancelDialogButton"),
  coverPreview: document.querySelector("#coverPreview"),
  paperCover: document.querySelector("#paperCover"),
  detailEmpty: document.querySelector("#detailEmpty"),
  detailCard: document.querySelector("#detailCard"),
  detailCover: document.querySelector("#detailCover"),
  detailStatus: document.querySelector("#detailStatus"),
  detailTitle: document.querySelector("#detailTitle"),
  detailMeta: document.querySelector("#detailMeta"),
  detailAbstract: document.querySelector("#detailAbstract"),
  detailTags: document.querySelector("#detailTags"),
  detailAiMeta: document.querySelector("#detailAiMeta"),
  detailTitleZh: document.querySelector("#detailTitleZh"),
  detailAiSummary: document.querySelector("#detailAiSummary"),
  detailDigestMeta: document.querySelector("#detailDigestMeta"),
  detailDigestPreview: document.querySelector("#detailDigestPreview"),
  detailReadingMeta: document.querySelector("#detailReadingMeta"),
  detailNotes: document.querySelector("#detailNotes"),
  detailLink: document.querySelector("#detailLink"),
  openDigestButton: document.querySelector("#openDigestButton"),
  editPaperButton: document.querySelector("#editPaperButton"),
  runAiButton: document.querySelector("#runAiButton"),
  openReaderButton: document.querySelector("#openReaderButton"),
  deletePaperActionButton: document.querySelector("#deletePaperActionButton"),
  favoritePaperButton: document.querySelector("#favoritePaperButton"),
  deletePaperButton: document.querySelector("#deletePaperButton"),
  saveNoteButton: document.querySelector("#saveNoteButton"),
  readerDialog: document.querySelector("#readerDialog"),
  readerTitle: document.querySelector("#readerTitle"),
  readerMeta: document.querySelector("#readerMeta"),
  readerProgress: document.querySelector("#readerProgress"),
  readerScroll: document.querySelector("#readerScroll"),
  readerSourceLink: document.querySelector("#readerSourceLink"),
  readerPrevButton: document.querySelector("#readerPrevButton"),
  readerNextButton: document.querySelector("#readerNextButton"),
  readerOriginalButton: document.querySelector("#readerOriginalButton"),
  readerTranslatedButton: document.querySelector("#readerTranslatedButton"),
  readerEmbeddedButton: document.querySelector("#readerEmbeddedButton"),
  readerDigestButton: document.querySelector("#readerDigestButton"),
  readerPretranslateButton: document.querySelector("#readerPretranslateButton"),
  readerDeleteButton: document.querySelector("#readerDeleteButton"),
  closeReaderButton: document.querySelector("#closeReaderButton"),
  digestDialog: document.querySelector("#digestDialog"),
  digestTitle: document.querySelector("#digestTitle"),
  digestMeta: document.querySelector("#digestMeta"),
  digestTakeaways: document.querySelector("#digestTakeaways"),
  digestAbstractZh: document.querySelector("#digestAbstractZh"),
  digestAbstractOriginal: document.querySelector("#digestAbstractOriginal"),
  digestMethodZh: document.querySelector("#digestMethodZh"),
  digestMethodOriginal: document.querySelector("#digestMethodOriginal"),
  digestConclusionZh: document.querySelector("#digestConclusionZh"),
  digestConclusionOriginal: document.querySelector("#digestConclusionOriginal"),
  refreshDigestButton: document.querySelector("#refreshDigestButton"),
  closeDigestButton: document.querySelector("#closeDigestButton"),
  providerDialog: document.querySelector("#providerDialog"),
  providerForm: document.querySelector("#providerForm"),
  providerSelect: document.querySelector("#providerSelect"),
  providerLabel: document.querySelector("#providerLabel"),
  providerDescription: document.querySelector("#providerDescription"),
  providerCapabilities: document.querySelector("#providerCapabilities"),
  providerModel: document.querySelector("#providerModel"),
  providerApiUrl: document.querySelector("#providerApiUrl"),
  providerApiKey: document.querySelector("#providerApiKey"),
  providerKeyHint: document.querySelector("#providerKeyHint"),
  providerClearApiKey: document.querySelector("#providerClearApiKey"),
  closeProviderButton: document.querySelector("#closeProviderButton"),
  cancelProviderButton: document.querySelector("#cancelProviderButton"),
  topicDiscoveryDialog: document.querySelector("#topicDiscoveryDialog"),
  topicDiscoveryForm: document.querySelector("#topicDiscoveryForm"),
  topicDiscoveryInput: document.querySelector("#topicDiscoveryInput"),
  topicDiscoveryLimit: document.querySelector("#topicDiscoveryLimit"),
  topicDiscoveryAutoDownloadCount: document.querySelector("#topicDiscoveryAutoDownloadCount"),
  topicDiscoveryMeta: document.querySelector("#topicDiscoveryMeta"),
  topicDiscoveryStrategy: document.querySelector("#topicDiscoveryStrategy"),
  topicDiscoveryResults: document.querySelector("#topicDiscoveryResults"),
  closeTopicDiscoveryButton: document.querySelector("#closeTopicDiscoveryButton"),
  cancelTopicDiscoveryButton: document.querySelector("#cancelTopicDiscoveryButton"),
  mapDialog: document.querySelector("#mapDialog"),
  mapMeta: document.querySelector("#mapMeta"),
  mapSummary: document.querySelector("#mapSummary"),
  mapInsights: document.querySelector("#mapInsights"),
  mapZoomOutButton: document.querySelector("#mapZoomOutButton"),
  mapZoomResetButton: document.querySelector("#mapZoomResetButton"),
  mapZoomInButton: document.querySelector("#mapZoomInButton"),
  mapCollapseAllButton: document.querySelector("#mapCollapseAllButton"),
  mapExpandAllButton: document.querySelector("#mapExpandAllButton"),
  mapSelectionTitle: document.querySelector("#mapSelectionTitle"),
  mapSelectionMeta: document.querySelector("#mapSelectionMeta"),
  mapSelectionCopy: document.querySelector("#mapSelectionCopy"),
  mapSelectionAction: document.querySelector("#mapSelectionAction"),
  mapCanvas: document.querySelector("#mapCanvas"),
  mapLibraryScopeButton: document.querySelector("#mapLibraryScopeButton"),
  mapPaperScopeButton: document.querySelector("#mapPaperScopeButton"),
  mapMindButton: document.querySelector("#mapMindButton"),
  mapGraphButton: document.querySelector("#mapGraphButton"),
  refreshMapButton: document.querySelector("#refreshMapButton"),
  closeMapButton: document.querySelector("#closeMapButton"),
  paperCardTemplate: document.querySelector("#paperCardTemplate")
};

init();

async function init() {
  if (window.location.protocol === "file:") {
    setNotice("请不要直接双击 `index.html`。先运行 `python server.py`，再打开 `http://127.0.0.1:8876`。");
    return;
  }
  bindEvents();
  await loadConfig();
  refreshPapers().catch(showError);
}

function bindEvents() {
  elements.searchInput.addEventListener("input", (event) => {
    state.filters.search = event.target.value.trim();
    render();
  });

  elements.statusFilter.addEventListener("change", (event) => {
    state.filters.status = event.target.value;
    render();
  });

  elements.collectionFilter.addEventListener("change", (event) => {
    state.filters.collection = event.target.value;
    render();
  });

  elements.favoriteFilter.addEventListener("change", (event) => {
    state.filters.favoritesOnly = event.target.checked;
    render();
  });

  elements.sortFilter.addEventListener("change", (event) => {
    state.filters.sort = event.target.value;
    render();
  });

  elements.newPaperButton.addEventListener("click", () => openDialog());
  elements.importButton.addEventListener("click", () => elements.importInput.click());
  elements.topicDiscoveryButton.addEventListener("click", () => openTopicDiscoveryDialog());
  elements.mapButton.addEventListener("click", () => openKnowledgeMapDialog(false));
  elements.providerSettingsButton.addEventListener("click", () => openProviderDialog());
  elements.importInput.addEventListener("change", handlePdfImport);
  elements.exportButton.addEventListener("click", exportLibrary);
  elements.seedButton.addEventListener("click", resetDatabase);
  elements.gridViewButton.addEventListener("click", () => setView("grid"));
  elements.listViewButton.addEventListener("click", () => setView("list"));
  elements.closeDialogButton.addEventListener("click", closeDialog);
  elements.cancelDialogButton.addEventListener("click", closeDialog);

  elements.editPaperButton.addEventListener("click", () => {
    const paper = getSelectedPaper();
    if (paper) openDialog(paper);
  });

  elements.runAiButton.addEventListener("click", async () => {
    const paper = getSelectedPaper();
    if (!paper) return;
    try {
      const updated = await api(`/api/papers/${paper.id}/ai-enrich`, { method: "POST" });
      state.selectedPaperId = updated.id;
      await refreshPapers();
      setNotice(`AI 已完成整理：${updated.title}`);
    } catch (error) {
      showError(error);
    }
  });

  elements.openReaderButton.addEventListener("click", async () => {
    const paper = getSelectedPaper();
    if (!paper) return;
    try {
      await openReader(paper);
    } catch (error) {
      showError(error);
    }
  });

  elements.openDigestButton.addEventListener("click", () => openDigestDialog(false));

  elements.favoritePaperButton.addEventListener("click", async () => {
    const paper = getSelectedPaper();
    if (!paper) return;
    await api(`/api/papers/${paper.id}`, {
      method: "PUT",
      body: JSON.stringify({
        favorite: !paper.favorite,
        updatedAt: new Date().toISOString()
      })
    });
    await refreshPapers();
  });

  elements.deletePaperButton.addEventListener("click", deleteSelectedPaper);
  elements.deletePaperActionButton.addEventListener("click", deleteSelectedPaper);
  elements.readerDeleteButton.addEventListener("click", deleteSelectedPaper);

  elements.saveNoteButton.addEventListener("click", async () => {
    const paper = getSelectedPaper();
    if (!paper) return;
    await api(`/api/papers/${paper.id}`, {
      method: "PUT",
      body: JSON.stringify({
        notes: elements.detailNotes.value.trim(),
        updatedAt: new Date().toISOString()
      })
    });
    await refreshPapers();
  });

  elements.paperForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await savePaper();
  });

  elements.closeReaderButton.addEventListener("click", closeReader);
  elements.readerPrevButton.addEventListener("click", () => jumpReaderPage(-1));
  elements.readerNextButton.addEventListener("click", () => jumpReaderPage(1));
  elements.readerOriginalButton.addEventListener("click", () => setReaderMode("original"));
  elements.readerTranslatedButton.addEventListener("click", () => setReaderMode("translated"));
  elements.readerEmbeddedButton.addEventListener("click", () => setReaderMode("embedded"));
  elements.readerDigestButton.addEventListener("click", () => openDigestDialog(false));
  elements.readerPretranslateButton.addEventListener("click", preloadReaderTranslation);
  elements.refreshDigestButton.addEventListener("click", () => openDigestDialog(true));
  elements.closeDigestButton.addEventListener("click", closeDigestDialog);
  elements.closeProviderButton.addEventListener("click", closeProviderDialog);
  elements.cancelProviderButton.addEventListener("click", closeProviderDialog);
  elements.providerSelect.addEventListener("change", handleProviderSelectionChange);
  elements.providerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveProviderConfig();
  });
  elements.closeTopicDiscoveryButton.addEventListener("click", closeTopicDiscoveryDialog);
  elements.cancelTopicDiscoveryButton.addEventListener("click", closeTopicDiscoveryDialog);
  elements.topicDiscoveryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runTopicDiscovery();
  });
  elements.mapLibraryScopeButton.addEventListener("click", () => setLibraryMapScope("library"));
  elements.mapPaperScopeButton.addEventListener("click", () => setLibraryMapScope("paper"));
  elements.mapMindButton.addEventListener("click", () => setLibraryMapView("mind"));
  elements.mapGraphButton.addEventListener("click", () => setLibraryMapView("graph"));
  elements.mapZoomOutButton.addEventListener("click", () => zoomKnowledgeMap(-0.12));
  elements.mapZoomResetButton.addEventListener("click", () => resetKnowledgeMapViewport(true));
  elements.mapZoomInButton.addEventListener("click", () => zoomKnowledgeMap(0.12));
  elements.mapCollapseAllButton.addEventListener("click", () => setAllMindMapThemesExpanded(false));
  elements.mapExpandAllButton.addEventListener("click", () => setAllMindMapThemesExpanded(true));
  elements.mapSelectionAction.addEventListener("click", openActiveKnowledgeMapPaper);
  elements.refreshMapButton.addEventListener("click", () => openKnowledgeMapDialog(true));
  elements.closeMapButton.addEventListener("click", closeKnowledgeMapDialog);
  elements.mapCanvas.addEventListener("click", handleKnowledgeMapClick);
  elements.mapCanvas.addEventListener("wheel", handleKnowledgeMapWheel, { passive: false });
  elements.mapCanvas.addEventListener("pointerdown", handleKnowledgeMapPointerDown);
  elements.mapCanvas.addEventListener("pointermove", handleKnowledgeMapPointerMove);
  elements.mapCanvas.addEventListener("pointerup", handleKnowledgeMapPointerUp);
  elements.mapCanvas.addEventListener("pointercancel", handleKnowledgeMapPointerUp);
  elements.mapCanvas.addEventListener("pointerleave", handleKnowledgeMapPointerLeave);

  elements.paperCover.addEventListener("change", async (event) => {
    const [file] = event.target.files;
    if (!file) {
      state.draftCoverImage = "";
      updateCoverPreview();
      return;
    }
    state.draftCoverImage = await fileToDataUrl(file);
    updateCoverPreview();
  });
}

async function refreshPapers() {
  state.papers = await api("/api/papers");
  if (!state.selectedPaperId && state.papers[0]) {
    state.selectedPaperId = state.papers[0].id;
  }
  if (state.selectedPaperId && !state.papers.some((paper) => paper.id === state.selectedPaperId)) {
    state.selectedPaperId = state.papers[0]?.id ?? null;
  }
  render();
}

async function loadConfig() {
  try {
    state.config = await api("/api/config");
  } catch {
    state.config = {
      openaiEnabled: false,
      openaiModel: "",
      aiEnabled: false,
      aiModel: "",
      aiProvider: "openai",
      aiProviderLabel: "OpenAI",
      supportsVisionTranslation: false,
      providerPresets: []
    };
  }
}

function render() {
  const visiblePapers = getVisiblePapers();
  renderStats();
  renderCollections();
  renderTags();
  renderReadingStack();
  renderViewToggle();
  renderGrid(visiblePapers);
  renderDetail();
  elements.resultMeta.textContent = `当前显示 ${visiblePapers.length} / ${state.papers.length} 篇论文`;
}

function renderStats() {
  const total = state.papers.length;
  const completed = state.papers.filter((paper) => paper.status === "completed").length;
  const favorites = state.papers.filter((paper) => paper.favorite).length;
  const pdfs = state.papers.filter((paper) => paper.pdfPath).length;
  const stats = [
    { label: "总论文", value: total },
    { label: "已读", value: completed },
    { label: "收藏", value: favorites },
    { label: "PDF", value: pdfs }
  ];

  elements.statGrid.innerHTML = stats.map((item) => `
    <article class="stat-card">
      <strong>${item.value}</strong>
      <span>${item.label}</span>
    </article>
  `).join("");
}

function renderCollections() {
  const collections = ["all", ...new Set(state.papers.map((paper) => paper.collection).filter(Boolean))];
  elements.collectionFilter.innerHTML = collections.map((collection) => {
    const label = collection === "all" ? "全部合集" : collection;
    const selected = state.filters.collection === collection ? "selected" : "";
    return `<option value="${escapeHtml(collection)}" ${selected}>${escapeHtml(label)}</option>`;
  }).join("");
}

function renderTags() {
  const tags = ["all", ...new Set(state.papers.flatMap((paper) => paper.tags || []))];
  elements.tagCloud.innerHTML = "";
  tags.forEach((tag) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tag-chip ${state.activeTag === tag ? "active" : ""}`;
    button.textContent = tag === "all" ? "全部标签" : tag;
    button.addEventListener("click", () => {
      state.activeTag = tag;
      render();
    });
    elements.tagCloud.append(button);
  });
}

function renderReadingStack() {
  const stack = state.papers
    .filter((paper) => paper.status === "reading" || paper.priority === "high")
    .sort((left, right) => new Date(right.updatedAt) - new Date(left.updatedAt))
    .slice(0, 4);

  if (stack.length === 0) {
    elements.readingStack.innerHTML = '<p class="library-empty">还没有在读或高优先论文。</p>';
    return;
  }

  elements.readingStack.innerHTML = stack.map((paper) => `
    <article class="mini-item">
      <strong>${escapeHtml(paper.title)}</strong>
      <span>${escapeHtml(paper.collection || "未分合集")}</span>
    </article>
  `).join("");
}

function renderViewToggle() {
  elements.gridViewButton.classList.toggle("active", state.view === "grid");
  elements.listViewButton.classList.toggle("active", state.view === "list");
}

function renderGrid(papers) {
  elements.paperGrid.classList.toggle("list-view", state.view === "list");

  if (papers.length === 0) {
    elements.paperGrid.innerHTML = `
      <div class="library-empty">
        <h3>没有匹配结果</h3>
        <p>试试清空筛选条件，或者导入一篇 PDF。</p>
      </div>
    `;
    return;
  }

  elements.paperGrid.innerHTML = "";
  papers.forEach((paper) => {
    const fragment = elements.paperCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".paper-card");
    const cover = fragment.querySelector(".paper-cover");
    const status = fragment.querySelector(".status-pill");
    const year = fragment.querySelector(".paper-year");
    const title = fragment.querySelector(".paper-title");
    const authors = fragment.querySelector(".paper-authors");
    const venue = fragment.querySelector(".paper-venue");
    const tags = fragment.querySelector(".paper-tags");
    const rating = fragment.querySelector(".rating-pill");
    const priority = fragment.querySelector(".priority-pill");
    const collection = fragment.querySelector(".collection-pill");

    applyCoverPresentation(cover, paper, "card");
    status.textContent = paper.favorite ? `★ ${statusText[paper.status] || "未分类"}` : (statusText[paper.status] || "未分类");
    year.textContent = paper.year || "未知年份";
    title.textContent = paper.title;
    authors.textContent = (paper.authors || []).join(", ") || "未知作者";
    venue.textContent = paper.venue || (paper.pdfPath ? "本地 PDF" : "未填写来源");
    rating.textContent = `${paper.rating || 0} / 5`;
    priority.textContent = priorityText[paper.priority] || "中优先";
    collection.textContent = paper.category || paper.collection || "未分合集";

    (paper.tags || []).slice(0, 4).forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = tag;
      tags.append(chip);
    });

    if (paper.readProgress) {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = `已读 ${paper.readProgress}%`;
      tags.append(chip);
    }

    card.addEventListener("click", async () => {
      state.selectedPaperId = paper.id;
      await api(`/api/papers/${paper.id}`, {
        method: "PUT",
        body: JSON.stringify({ updatedAt: new Date().toISOString() })
      });
      await refreshPapers();
    });

    if (paper.id === state.selectedPaperId) {
      card.style.outline = "3px solid rgba(169, 92, 56, 0.48)";
      card.style.outlineOffset = "1px";
    }

    elements.paperGrid.append(fragment);
  });
}

function renderDetail() {
  const paper = getSelectedPaper();
  if (!paper) {
    elements.detailEmpty.classList.remove("hidden");
    elements.detailCard.classList.add("hidden");
    return;
  }

  elements.detailEmpty.classList.add("hidden");
  elements.detailCard.classList.remove("hidden");

  applyCoverPresentation(elements.detailCover, paper, "detail");
  elements.detailStatus.textContent = `${paper.category || paper.collection || "未分类"} · ${statusText[paper.status] || "未分类"}`;
  elements.detailTitle.textContent = paper.title;
  elements.detailAbstract.textContent = paper.abstract || "暂无摘要。";
  elements.detailTitleZh.textContent = paper.titleZh ? `中文标题：${paper.titleZh}` : "还没有中文标题翻译。";
  elements.detailAiSummary.textContent = paper.aiSummaryZh || paper.aiSummary || "还没有 AI 摘要。";
  elements.detailNotes.value = paper.notes || "";
  elements.detailLink.href = paper.url || paper.pdfUrl || "#";
  elements.detailLink.textContent = paper.pdfUrl ? "打开 PDF" : "打开链接";
  elements.detailLink.style.pointerEvents = paper.url || paper.pdfUrl ? "auto" : "none";
  elements.detailLink.style.opacity = paper.url || paper.pdfUrl ? "1" : "0.45";
  elements.favoritePaperButton.textContent = paper.favorite ? "★" : "☆";
  elements.runAiButton.disabled = !state.config.aiEnabled;
  elements.runAiButton.textContent = state.config.aiEnabled ? "AI 整理" : "AI 未配置";
  elements.openReaderButton.disabled = !paper.pdfPath;

  const meta = [
    (paper.authors || []).join(", ") || "未知作者",
    paper.year || "未知年份",
    paper.venue || "未填写来源",
    `DOI: ${paper.doi || "暂无"}`,
    `优先级: ${priorityText[paper.priority] || "中优先"}`,
    `评分: ${paper.rating || 0} / 5`
  ];
  if (paper.originalFilename) {
    meta.push(`文件: ${paper.originalFilename}`);
  }

  elements.detailMeta.innerHTML = meta.map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`).join("");
  elements.detailAiMeta.innerHTML = [
    paper.category ? `分类: ${paper.category}` : "",
    paper.aiConfidence ? `AI 置信度: ${Math.round(paper.aiConfidence * 100)}%` : "",
    paper.aiModel ? `模型: ${paper.aiModel}` : "",
    paper.aiEnrichedAt ? `整理时间: ${paper.aiEnrichedAt}` : ""
  ]
    .filter(Boolean)
    .map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`)
    .join("");
  const digest = state.digests[paper.id];
  elements.detailDigestMeta.innerHTML = digest
    ? [
        digest.source === "ai" ? "来源: AI 整理" : "来源: 本地提取",
        digest.aiModel ? `模型: ${digest.aiModel}` : "",
        digest.updatedAt ? `时间: ${digest.updatedAt}` : ""
      ]
        .filter(Boolean)
        .map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`)
        .join("")
    : '<span class="meta-chip">可生成 Abstract / Method / Conclusion 精华</span>';
  elements.detailDigestPreview.textContent = digest
    ? (digest.takeawaysZh?.[0] || digest.abstract?.zh || digest.abstract?.original || "已生成论文精华。")
    : "点击“查看”，生成论文的 Abstract、Method、Conclusion 精华翻译。";
  elements.detailReadingMeta.innerHTML = [
    paper.readerTotalPages ? `阅读页数: ${paper.readerPage || 1} / ${paper.readerTotalPages}` : "未开始阅读",
    paper.readProgress ? `进度: ${paper.readProgress}%` : "",
    paper.lastReadAt ? `上次阅读: ${paper.lastReadAt}` : ""
  ]
    .filter(Boolean)
    .map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`)
    .join("");
  elements.detailTags.innerHTML = "";
  (paper.tags || []).forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = tag;
    elements.detailTags.append(chip);
  });
  (paper.aiKeywords || []).forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = `AI:${tag}`;
    elements.detailTags.append(chip);
  });
}

function openDialog(paper = null) {
  state.editingPaperId = paper?.id ?? null;
  state.draftCoverImage = paper?.coverImage || "";
  elements.dialogTitle.textContent = paper ? "编辑论文" : "新增论文";
  elements.paperForm.reset();

  setValue("paperTitle", paper?.title || "");
  setValue("paperAuthors", (paper?.authors || []).join(", "));
  setValue("paperYear", paper?.year || "");
  setValue("paperVenue", paper?.venue || "");
  setValue("paperDoi", paper?.doi || "");
  setValue("paperUrl", paper?.url || "");
  setValue("paperStatus", paper?.status || "to-read");
  setValue("paperPriority", paper?.priority || "medium");
  setValue("paperRating", paper?.rating || "");
  setValue("paperTags", (paper?.tags || []).join(", "));
  setValue("paperCollection", paper?.collection || "");
  setValue("paperAbstract", paper?.abstract || "");
  setValue("paperNotes", paper?.notes || "");
  document.querySelector("#paperFavorite").checked = Boolean(paper?.favorite);
  updateCoverPreview();
  elements.paperDialog.showModal();
}

function closeDialog() {
  state.editingPaperId = null;
  state.draftCoverImage = "";
  elements.paperDialog.close();
}

async function savePaper() {
  const formData = new FormData(elements.paperForm);
  const payload = {
    title: normalizeString(formData.get("title")),
    authors: parseCommaSeparated(formData.get("authors")),
    year: normalizeNumber(formData.get("year")),
    venue: normalizeString(formData.get("venue")),
    doi: normalizeString(formData.get("doi")),
    url: normalizeString(formData.get("url")),
    status: normalizeString(formData.get("status")) || "to-read",
    priority: normalizeString(formData.get("priority")) || "medium",
    rating: normalizeNumber(formData.get("rating")),
    favorite: document.querySelector("#paperFavorite").checked,
    collection: normalizeString(formData.get("collection")),
    tags: parseCommaSeparated(formData.get("tags")),
    abstract: normalizeString(formData.get("abstract")),
    notes: normalizeString(formData.get("notes")),
    coverImage: state.draftCoverImage || "",
    updatedAt: new Date().toISOString()
  };

  if (!payload.title) return;

  if (state.editingPaperId) {
    await api(`/api/papers/${state.editingPaperId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  } else {
    await api("/api/papers", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  closeDialog();
  await refreshPapers();
}

async function handlePdfImport(event) {
  const [file] = event.target.files;
  if (!file) return;
  try {
    const formData = new FormData();
    formData.append("file", file);
    const createdPaper = await api("/api/papers/import-pdf", {
      method: "POST",
      body: formData,
      isForm: true
    });
    state.selectedPaperId = createdPaper.id;
    await refreshPapers();
    setNotice(`已自动提取标题、封面和标签：${createdPaper.title}`);
  } catch (error) {
    showError(error);
  } finally {
    event.target.value = "";
  }
}

async function legacyOpenReader(paper) {
  if (!paper.pdfPath) {
    setNotice("这篇论文没有本地 PDF，暂时不能在应用内阅读。");
    return;
  }

  const reader = await api(`/api/papers/${paper.id}/reader`);
  state.reader.paperId = paper.id;
  state.reader.pages = reader.pages || [];
  state.reader.currentPage = reader.currentPage || 1;
  state.reader.mode = state.config.aiEnabled ? "translated" : "original";
  state.reader.translations = {};
  state.reader.loadingPages = new Set();
  state.reader.translationJob = null;
  state.reader.translationLoadedPages = 0;
  stopReaderTranslationJobPolling();
  elements.readerTitle.textContent = paper.titleZh || paper.title;
  elements.readerSourceLink.href = reader.pdfUrl || "#";
  renderReaderPages();
  renderReaderModeButtons();
  updateReaderMeta();
  elements.readerDialog.showModal();
  try {
    state.reader.translationJob = await api(`/api/papers/${paper.id}/reader-translation-job`);
    await refreshReaderTranslations();
    if (state.reader.translationJob.status === "running" || state.reader.translationJob.status === "queued") {
      state.reader.translationJobTimer = window.setInterval(pollReaderTranslationJob, 1200);
    }
  } catch {}
  requestAnimationFrame(() => {
    scrollReaderToPage(state.reader.currentPage, false);
    if (state.reader.mode !== "original") {
      ensureReaderTranslation(state.reader.currentPage);
      ensureReaderTranslation(state.reader.currentPage + 1);
    }
  });
}

async function deleteSelectedPaper() {
  const paper = getSelectedPaper();
  if (!paper) return;
  if (!confirm(`确认删除《${paper.title}》吗？`)) return;
  if (state.reader.paperId === paper.id) {
    closeReader();
  }
  await api(`/api/papers/${paper.id}`, { method: "DELETE" });
  state.selectedPaperId = null;
  await refreshPapers();
  setNotice(`已删除论文：${paper.title}`);
}

function legacyRenderReaderPages() {
  if (state.reader.observer) {
    state.reader.observer.disconnect();
  }
  elements.readerScroll.innerHTML = "";
  state.reader.pages.forEach((page) => {
    const article = document.createElement("article");
    article.className = "reader-page";
    article.dataset.page = String(page.page);
    article.innerHTML = `
      <div class="reader-page-head">第 ${page.page} 页</div>
      <div class="reader-page-frame">
        <img src="${page.imageUrl}" alt="PDF page ${page.page}" loading="lazy">
        <div class="reader-translation-holder"></div>
      </div>
      <div class="reader-clean-panel"></div>
    `;
    elements.readerScroll.append(article);
  });

  state.reader.observer = new IntersectionObserver(handleReaderIntersection, {
    root: elements.readerScroll,
    threshold: 0.6
  });
  elements.readerScroll.querySelectorAll(".reader-page").forEach((node) => {
    state.reader.observer.observe(node);
  });
  renderReaderCleanPanels();
  renderReaderTranslationLayers();
}

function legacyHandleReaderIntersection(entries) {
  const visible = entries
    .filter((entry) => entry.isIntersecting)
    .sort((left, right) => Number(left.target.dataset.page) - Number(right.target.dataset.page));
  if (!visible[0]) return;
  const page = Number(visible[0].target.dataset.page);
  if (!page || page === state.reader.currentPage) return;
  state.reader.currentPage = page;
  updateReaderMeta();
  if (state.reader.mode !== "original") {
    ensureReaderTranslation(page);
    ensureReaderTranslation(page + 1);
  }
  scheduleReaderStateSave();
}

function jumpReaderPage(step) {
  if (!state.reader.pages.length) return;
  const nextPage = Math.min(
    state.reader.pages.length,
    Math.max(1, state.reader.currentPage + step)
  );
  scrollReaderToPage(nextPage, true);
}

function legacyScrollReaderToPage(page, smooth = true) {
  const node = elements.readerScroll.querySelector(`[data-page="${page}"]`);
  if (!node) return;
  node.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
  state.reader.currentPage = page;
  updateReaderMeta();
  if (state.reader.mode !== "original") {
    ensureReaderTranslation(page);
    ensureReaderTranslation(page + 1);
  }
  scheduleReaderStateSave();
}

function scheduleReaderStateSave() {
  if (!state.reader.paperId) return;
  window.clearTimeout(state.reader.saveTimer);
  state.reader.saveTimer = window.setTimeout(async () => {
    const updated = await api(`/api/papers/${state.reader.paperId}/reader-state`, {
      method: "PUT",
      body: JSON.stringify({
        readerPage: state.reader.currentPage,
        readerTotalPages: state.reader.pages.length,
        readerScroll: elements.readerScroll.scrollTop / Math.max(1, elements.readerScroll.scrollHeight - elements.readerScroll.clientHeight)
      })
    });
    const index = state.papers.findIndex((paper) => paper.id === updated.id);
    if (index >= 0) state.papers[index] = updated;
    renderDetail();
  }, 500);
}

function closeReader() {
  if (state.reader.observer) {
    state.reader.observer.disconnect();
    state.reader.observer = null;
  }
  window.clearInterval(state.reader.translationJobTimer);
  window.clearTimeout(state.reader.saveTimer);
  state.reader.paperId = null;
  state.reader.pages = [];
  state.reader.currentPage = 1;
  state.reader.mode = "original";
  state.reader.translations = {};
  state.reader.loadingPages = new Set();
  state.reader.translationJob = null;
  state.reader.translationJobTimer = null;
  state.reader.translationLoadedPages = 0;
  elements.readerScroll.innerHTML = "";
  elements.readerProgress.innerHTML = "";
  elements.readerProgress.classList.add("hidden");
  elements.readerDialog.close();
}

function legacyUpdateReaderMeta() {
  const total = state.reader.pages.length;
  const modeLabel = state.reader.mode === "translated" ? "中文阅读" : "原文";
  elements.readerMeta.textContent = total ? `${state.reader.currentPage} / ${total} · ${modeLabel}` : modeLabel;
}

function legacyRenderReaderModeButtons() {
  elements.readerOriginalButton.classList.toggle("active", state.reader.mode === "original");
  elements.readerTranslatedButton.classList.toggle("active", state.reader.mode === "translated");
  elements.readerPretranslateButton.disabled = !state.config.aiEnabled || !state.reader.paperId;
  updateReaderMeta();
  renderReaderTranslationLayers();
}

function legacySetReaderMode(mode) {
  state.reader.mode = mode;
  renderReaderModeButtons();
  if (mode === "translated") {
    ensureReaderTranslation(state.reader.currentPage);
    ensureReaderTranslation(state.reader.currentPage + 1);
  }
}

async function legacyEnsureReaderTranslation(pageNumber) {
  if (state.reader.mode !== "translated") return;
  if (!state.reader.paperId) return;
  if (!Number.isInteger(pageNumber) || pageNumber < 1 || pageNumber > state.reader.pages.length) return;
  if (state.reader.translations[pageNumber] || state.reader.loadingPages.has(pageNumber)) return;

  state.reader.loadingPages.add(pageNumber);
  try {
    const payload = await api(`/api/papers/${state.reader.paperId}/reader-translation?page=${pageNumber}`);
    state.reader.translations[pageNumber] = payload;
    renderReaderTranslationLayers();
  } catch (error) {
    if (state.reader.mode === "translated") {
      state.reader.mode = "original";
      renderReaderModeButtons();
      setNotice(`中文阅读暂时不可用：${error.message}`);
    }
  } finally {
    state.reader.loadingPages.delete(pageNumber);
  }
}

async function legacyPreloadReaderTranslation() {
  if (!state.reader.paperId) return;
  elements.readerPretranslateButton.disabled = true;
  const originalLabel = elements.readerPretranslateButton.textContent;
  elements.readerPretranslateButton.textContent = "翻译中...";
  try {
    const result = await api(`/api/papers/${state.reader.paperId}/reader-translation/preload`, {
      method: "POST",
      body: JSON.stringify({})
    });
    state.reader.mode = "translated";
    const pageNumbers = Array.from({ length: result.totalPages || state.reader.pages.length }, (_, index) => index + 1);
    await Promise.all(pageNumbers.map((pageNumber) => ensureReaderTranslation(pageNumber)));
    renderReaderModeButtons();
    setNotice(`已完成全文预翻译：${result.translatedPages} 页`);
  } catch (error) {
    showError(error);
  } finally {
    elements.readerPretranslateButton.textContent = originalLabel;
    renderReaderModeButtons();
  }
}

function legacyRenderReaderTranslationLayers() {
  elements.readerScroll.querySelectorAll(".reader-page").forEach((node) => {
    const pageNumber = Number(node.dataset.page);
    const holder = node.querySelector(".reader-translation-holder");
    if (!holder) return;
    const translation = state.reader.translations[pageNumber];
    const shouldShow = state.reader.mode === "translated" && translation;
    node.classList.toggle("translated", Boolean(shouldShow));
    if (!shouldShow) {
      holder.innerHTML = "";
      return;
    }
    holder.innerHTML = buildReaderTranslationSvg(translation);
  });
}

function buildReaderTranslationSvg(translation) {
  const width = Number(translation.width) || 1;
  const height = Number(translation.height) || 1;
  const blocks = Array.isArray(translation.blocks) ? translation.blocks : [];
  const content = blocks
    .filter((block) => normalizeString(block.text))
    .map((block) => {
      const x = Number(block.x) || 0;
      const y = Number(block.y) || 0;
      const blockWidth = Math.max(1, Number(block.width) || 0);
      const blockHeight = Math.max(1, Number(block.height) || 0);
      const fontSize = Math.max(10, Number(block.fontSize) || 12);
      const text = escapeXml(String(block.text)).replaceAll("\n", "<br/>");
      return `
        <foreignObject x="${x}" y="${y}" width="${blockWidth}" height="${blockHeight}">
          <div xmlns="http://www.w3.org/1999/xhtml"
            style="width:100%;height:100%;padding:2px 4px;box-sizing:border-box;overflow:hidden;border-radius:6px;background:rgba(255,250,242,0.94);color:#1d2622;font-size:${fontSize}px;line-height:1.28;">
            ${text}
          </div>
        </foreignObject>
      `;
    })
    .join("");

  return `
    <svg class="reader-translation-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      ${content}
    </svg>
  `;
}

async function openDigestDialog(refresh = false) {
  const paper = getSelectedPaper();
  if (!paper) return;
  elements.digestTitle.textContent = paper.titleZh || paper.title;
  elements.digestMeta.textContent = refresh ? "正在重新整理论文精华..." : "正在加载论文精华...";
  elements.digestTakeaways.innerHTML = "";
  elements.digestAbstractZh.textContent = "";
  elements.digestAbstractOriginal.textContent = "";
  elements.digestMethodZh.textContent = "";
  elements.digestMethodOriginal.textContent = "";
  elements.digestConclusionZh.textContent = "";
  elements.digestConclusionOriginal.textContent = "";
  elements.digestDialog.showModal();
  try {
    const digest = refresh
      ? await api(`/api/papers/${paper.id}/digest`, { method: "POST", body: JSON.stringify({}) })
      : await api(`/api/papers/${paper.id}/digest`);
    state.digests[paper.id] = digest;
    renderDigestDialog(digest);
    renderDetail();
  } catch (error) {
    elements.digestMeta.textContent = `加载失败：${error.message}`;
    showError(error);
  }
}

function renderDigestDialog(digest) {
  elements.digestMeta.textContent = [
    digest.source === "ai" ? "来源: AI 整理" : "来源: 本地提取",
    digest.aiModel ? `模型: ${digest.aiModel}` : "",
    digest.updatedAt ? `更新时间: ${digest.updatedAt}` : ""
  ].filter(Boolean).join(" · ");

  elements.digestTakeaways.innerHTML = "";
  (digest.takeawaysZh || []).forEach((item) => {
    const chip = document.createElement("div");
    chip.className = "digest-bullet";
    chip.textContent = item;
    elements.digestTakeaways.append(chip);
  });

  elements.digestAbstractZh.textContent = digest.abstract?.zh || "暂无中文整理。";
  elements.digestAbstractOriginal.textContent = digest.abstract?.original || "暂无原文片段。";
  elements.digestMethodZh.textContent = digest.method?.zh || "暂无 Method 整理。";
  elements.digestMethodOriginal.textContent = digest.method?.original || "暂无原文片段。";
  elements.digestConclusionZh.textContent = digest.conclusion?.zh || "暂无 Conclusion 整理。";
  elements.digestConclusionOriginal.textContent = digest.conclusion?.original || "暂无原文片段。";
}

function closeDigestDialog() {
  elements.digestDialog.close();
}

async function openProviderDialog() {
  const payload = await api("/api/provider-config");
  state.providerConfig = payload;
  renderProviderDialog();
  elements.providerDialog.showModal();
}

function closeProviderDialog() {
  elements.providerDialog.close();
}

function openTopicDiscoveryDialog() {
  renderTopicDiscoveryResults();
  elements.topicDiscoveryDialog.showModal();
}

function closeTopicDiscoveryDialog() {
  elements.topicDiscoveryDialog.close();
}

async function runTopicDiscovery() {
  const topic = normalizeString(elements.topicDiscoveryInput.value);
  const limit = Math.min(20, Math.max(3, normalizeNumber(elements.topicDiscoveryLimit.value) || 10));
  const autoDownloadCount = Math.min(10, Math.max(0, Number(elements.topicDiscoveryAutoDownloadCount.value) || 0));
  if (!topic) {
    setNotice("请先输入研究主题。");
    return;
  }

  elements.topicDiscoveryMeta.textContent = `正在检索“${topic}”相关论文并自动下载推荐 PDF...`;
  elements.topicDiscoveryStrategy.innerHTML = "";
  elements.topicDiscoveryResults.innerHTML = '<div class="map-empty"><div><h3>正在检索</h3><p>系统会抓取开放 PDF、做 CRAAP 评分，并给出推荐阅读顺序。</p></div></div>';

  try {
    const payload = await api("/api/topic-discovery", {
      method: "POST",
      body: JSON.stringify({ topic, limit, autoDownloadCount })
    });
    state.topicDiscovery.payload = payload;
    renderTopicDiscoveryResults();
    if ((payload.importedCount || 0) + (payload.updatedCount || 0) > 0) {
      await refreshPapers();
      const imported = (payload.results || []).find((item) => item.paperId);
      if (imported?.paperId) state.selectedPaperId = imported.paperId;
      render();
    }
    setNotice(
      `主题发现完成：新增 ${payload.importedCount || 0} 篇，更新 ${payload.updatedCount || 0} 篇，跳过 ${payload.existingCount || 0} 篇。`
    );
  } catch (error) {
    elements.topicDiscoveryMeta.textContent = `检索失败：${error.message}`;
    elements.topicDiscoveryResults.innerHTML = '<div class="map-empty"><div><h3>检索失败</h3><p>请检查网络连通性，或缩小主题范围后重试。</p></div></div>';
    showError(error);
  }
}

function renderTopicDiscoveryResults() {
  const payload = state.topicDiscovery.payload;
  if (!payload) {
    elements.topicDiscoveryMeta.textContent = "输入主题后，系统会检索开放 PDF 论文并自动导入推荐结果。";
    elements.topicDiscoveryStrategy.innerHTML = "";
    elements.topicDiscoveryResults.innerHTML = '<div class="map-empty"><div><h3>暂无检索结果</h3><p>输入一个主题后，这里会展示 CRAAP 评分、下载状态和推荐阅读顺序。</p></div></div>';
    return;
  }

  elements.topicDiscoveryMeta.textContent = [
    `来源: ${payload.source || "arXiv"}`,
    payload.searchQuery ? `检索词: ${payload.searchQuery}` : "",
    payload.evaluationSource === "ai"
      ? `评估: AI${payload.evaluationModel ? ` (${payload.evaluationModel})` : ""}`
      : "评估: 本地规则回退",
    `候选: ${(payload.results || []).length}`,
    `自动下载: ${payload.autoDownloadCount || 0}`,
    payload.warning || ""
  ].filter(Boolean).join(" · ");

  elements.topicDiscoveryStrategy.innerHTML = "";
  (payload.readingStrategy || []).forEach((item) => {
    const chip = document.createElement("div");
    chip.className = "digest-bullet";
    chip.textContent = item;
    elements.topicDiscoveryStrategy.append(chip);
  });

  const results = payload.results || [];
  if (!results.length) {
    elements.topicDiscoveryResults.innerHTML = '<div class="map-empty"><div><h3>没有找到结果</h3><p>可以改用更具体的英文关键词，或者先配置 AI Provider 用于中文主题改写。</p></div></div>';
    return;
  }

  elements.topicDiscoveryResults.innerHTML = results.map((item) => {
    const craap = item.craap || {};
    const statusClass = normalizeString(item.importStatus || "pending");
    const authors = (item.authors || []).slice(0, 4).join(", ");
    return `
      <article class="topic-result-card">
        <div class="topic-result-head">
          <div class="topic-rank-badge">推荐 ${escapeHtml(item.recommendedOrder)}</div>
          <div class="detail-meta">
            <span class="meta-chip">CRAAP ${escapeHtml(craap.total || 0)}/100</span>
            <span class="meta-chip">${escapeHtml(item.readingStage || "frontier")}</span>
            <span class="meta-chip">${escapeHtml(item.year || "未知年份")}</span>
          </div>
        </div>
        <h4>${escapeHtml(item.title || "Untitled")}</h4>
        <p class="topic-result-meta">${escapeHtml(authors || "未知作者")} · ${escapeHtml(item.sourceLabel || "arXiv")}</p>
        <p class="topic-result-summary">${escapeHtml(item.summary || "暂无摘要。")}</p>
        <div class="detail-meta">
          <span class="meta-chip">C ${escapeHtml(craap.currency || 0)}</span>
          <span class="meta-chip">R ${escapeHtml(craap.relevance || 0)}</span>
          <span class="meta-chip">A ${escapeHtml(craap.authority || 0)}</span>
          <span class="meta-chip">A ${escapeHtml(craap.accuracy || 0)}</span>
          <span class="meta-chip">P ${escapeHtml(craap.purpose || 0)}</span>
        </div>
        <p class="topic-result-reason">${escapeHtml(item.recommendationReason || "")}</p>
        <div class="topic-result-footer">
          <span class="topic-import-status ${escapeHtml(statusClass)}">${escapeHtml(item.importStatus || "pending")}</span>
          <span class="topic-result-message">${escapeHtml(item.importMessage || "")}</span>
        </div>
        <div class="hero-actions">
          ${item.url ? `<a class="secondary-button" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">摘要页</a>` : ""}
          ${item.pdfUrl ? `<a class="secondary-button" href="${escapeHtml(item.pdfUrl)}" target="_blank" rel="noreferrer">PDF</a>` : ""}
          ${item.paperId ? `<button class="secondary-button" type="button" data-open-paper-id="${escapeHtml(item.paperId)}">定位到论文</button>` : ""}
        </div>
      </article>
    `;
  }).join("");

  elements.topicDiscoveryResults.querySelectorAll("[data-open-paper-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const paperId = button.getAttribute("data-open-paper-id");
      if (!paperId) return;
      state.selectedPaperId = paperId;
      closeTopicDiscoveryDialog();
      render();
    });
  });
}

async function openKnowledgeMapDialog(refresh = false) {
  elements.mapMeta.textContent = refresh ? "正在重新生成知识地图..." : "正在加载知识地图...";
  elements.mapSummary.textContent = "系统会基于当前论文库整理主题脉络、关键概念和主题关系。";
  elements.mapInsights.innerHTML = "";
  elements.mapSelectionTitle.textContent = "Paper Hub 论文知识地图";
  elements.mapSelectionMeta.textContent = "";
  elements.mapSelectionCopy.textContent = "在图中悬停或点击节点，可以查看主题、概念和论文之间的关系。";
  elements.mapSelectionAction.classList.add("hidden");
  elements.mapCanvas.innerHTML = '<div class="map-empty"><div><h3>正在构建知识地图</h3><p>这一步会汇总当前论文库并尝试生成全库主题结构。</p></div></div>';
  elements.mapDialog.showModal();
  try {
    const paperId = currentLibraryMapPaperId();
    const payload = refresh
      ? await api("/api/library-map", { method: "POST", body: JSON.stringify({ paperId }) })
      : await api(`/api/library-map${paperId ? `?paperId=${encodeURIComponent(paperId)}` : ""}`);
    setKnowledgeMapPayload(payload, true);
    renderKnowledgeMap();
  } catch (error) {
    elements.mapMeta.textContent = `加载失败：${error.message}`;
    elements.mapCanvas.innerHTML = '<div class="map-empty"><div><h3>知识地图生成失败</h3><p>请检查本地服务或 AI Provider 配置。</p></div></div>';
    showError(error);
  }
}

function closeKnowledgeMapDialog() {
  releaseKnowledgeMapPointer();
  elements.mapDialog.close();
}

function currentLibraryMapPaperId() {
  return state.libraryMap.scope === "paper" ? (state.selectedPaperId || "") : "";
}

function setLibraryMapScope(scope) {
  state.libraryMap.scope = scope;
  if (elements.mapDialog.open) {
    openKnowledgeMapDialog(false);
  } else {
    renderKnowledgeMap();
  }
}

function setLibraryMapView(view) {
  if (state.libraryMap.view === view) return;
  state.libraryMap.view = view;
  state.libraryMap.viewport = createLibraryMapViewport(view);
  renderKnowledgeMap();
}

function handleKnowledgeMapClick(event) {
  const node = event.target.closest("[data-node-id]");
  if (!node) return;
  const nodeId = node.getAttribute("data-node-id");
  if (!nodeId) return;
  const role = node.getAttribute("data-node-role") || "";
  state.libraryMap.activeNodeId = nodeId;
  state.libraryMap.hoveredNodeId = "";
  if (role === "theme" && state.libraryMap.view === "mind") {
    toggleMindMapTheme(nodeId);
    return;
  }
  if ((event.metaKey || event.ctrlKey) && node.getAttribute("data-paper-id")) {
    openPaperFromKnowledgeMap(node.getAttribute("data-paper-id"));
    return;
  }
  renderKnowledgeMap();
}

function handleKnowledgeMapWheel(event) {
  const stage = event.target.closest("[data-map-stage]");
  if (!stage) return;
  event.preventDefault();
  const delta = event.deltaY > 0 ? -0.08 : 0.08;
  zoomKnowledgeMap(delta, event.clientX, event.clientY);
}

function handleKnowledgeMapPointerDown(event) {
  const stage = event.target.closest("[data-map-stage]");
  if (!stage || event.target.closest("[data-node-id]")) return;
  state.libraryMap.viewport.panning = true;
  state.libraryMap.viewport.pointerId = event.pointerId;
  state.libraryMap.viewport.startX = event.clientX;
  state.libraryMap.viewport.startY = event.clientY;
  state.libraryMap.viewport.originX = state.libraryMap.viewport.x;
  state.libraryMap.viewport.originY = state.libraryMap.viewport.y;
  stage.setPointerCapture?.(event.pointerId);
  syncKnowledgeMapViewport();
}

function handleKnowledgeMapPointerMove(event) {
  const hoveredNode = event.target.closest("[data-node-id]");
  const hoveredNodeId = hoveredNode?.getAttribute("data-node-id") || "";
  if (hoveredNodeId !== state.libraryMap.hoveredNodeId) {
    state.libraryMap.hoveredNodeId = hoveredNodeId;
    syncKnowledgeMapSelection();
  }
  if (!state.libraryMap.viewport.panning || state.libraryMap.viewport.pointerId !== event.pointerId) return;
  state.libraryMap.viewport.x = state.libraryMap.viewport.originX + (event.clientX - state.libraryMap.viewport.startX);
  state.libraryMap.viewport.y = state.libraryMap.viewport.originY + (event.clientY - state.libraryMap.viewport.startY);
  syncKnowledgeMapViewport();
}

function handleKnowledgeMapPointerUp(event) {
  if (state.libraryMap.viewport.pointerId !== event.pointerId) return;
  releaseKnowledgeMapPointer();
}

function handleKnowledgeMapPointerLeave() {
  state.libraryMap.hoveredNodeId = "";
  syncKnowledgeMapSelection();
  if (state.libraryMap.viewport.panning) {
    releaseKnowledgeMapPointer();
  }
}

function renderKnowledgeMap() {
  const payload = state.libraryMap.payload;
  const hasSelectedPaper = Boolean(state.selectedPaperId && getSelectedPaper());
  if (state.libraryMap.scope === "paper" && !hasSelectedPaper) {
    state.libraryMap.scope = "library";
  }
  elements.mapLibraryScopeButton.classList.toggle("active", state.libraryMap.scope === "library");
  elements.mapPaperScopeButton.classList.toggle("active", state.libraryMap.scope === "paper");
  elements.mapPaperScopeButton.disabled = !hasSelectedPaper;
  elements.mapMindButton.classList.toggle("active", state.libraryMap.view === "mind");
  elements.mapGraphButton.classList.toggle("active", state.libraryMap.view === "graph");
  elements.mapZoomOutButton.disabled = !payload;
  elements.mapZoomResetButton.disabled = !payload;
  elements.mapZoomInButton.disabled = !payload;
  elements.mapCollapseAllButton.disabled = state.libraryMap.view !== "mind" || !payload;
  elements.mapExpandAllButton.disabled = state.libraryMap.view !== "mind" || !payload;
  if (!payload) {
    elements.mapMeta.textContent = "还没有知识地图数据。";
    elements.mapSummary.textContent = "导入论文后即可生成。";
    elements.mapInsights.innerHTML = "";
    elements.mapCanvas.innerHTML = '<div class="map-empty"><div><h3>暂无数据</h3><p>请先导入论文，或点击“重新生成”。</p></div></div>';
    syncKnowledgeMapSelection();
    return;
  }

  if (!state.libraryMap.nodeIndex.size) {
    rebuildKnowledgeMapNodeIndex(payload);
  }
  const stats = payload.stats || {};
  elements.mapMeta.textContent = [
    payload.scope?.mode === "paper" ? `作用域: ${payload.scope?.label || "当前论文"}` : "作用域: 整个论文库",
    payload.source === "ai" ? "来源: AI 生成" : "来源: 本地规则",
    payload.aiModel ? `模型: ${payload.aiModel}` : "",
    stats.paperCount ? `论文: ${stats.paperCount}` : "论文: 0",
    stats.themeCount ? `主题: ${stats.themeCount}` : "",
    payload.updatedAt ? `更新时间: ${payload.updatedAt}` : ""
  ].filter(Boolean).join(" · ");
  elements.mapSummary.textContent = payload.summaryZh || "系统已根据当前论文库生成全库知识地图。";
  elements.mapInsights.innerHTML = "";
  (payload.insightsZh || []).forEach((item) => {
    const chip = document.createElement("div");
    chip.className = "digest-bullet";
    chip.textContent = item;
    elements.mapInsights.append(chip);
  });
  if (payload.message) {
    const chip = document.createElement("div");
    chip.className = "digest-bullet";
    chip.textContent = payload.message;
    elements.mapInsights.append(chip);
  }

  if (state.libraryMap.view === "graph") {
    elements.mapCanvas.innerHTML = renderKnowledgeGraphView(payload.knowledgeGraph || {});
  } else {
    elements.mapCanvas.innerHTML = renderMindMapView(payload.mindMap || {});
  }
  syncKnowledgeMapViewport();
  syncKnowledgeMapSelection();
}

function renderMindMapView(mindMap) {
  const layout = layoutMindMap(mindMap);
  if (!layout.nodes.length) {
    return '<div class="map-empty"><div><h3>暂无主题</h3><p>当前论文库还不足以生成稳定的主题结构。</p></div></div>';
  }
  return `
    <div class="map-stage" data-map-stage>
      <div class="map-scene" data-map-scene style="width:${layout.width}px; height:${layout.height}px;">
        <svg viewBox="0 0 ${layout.width} ${layout.height}" role="img" aria-label="Interactive mind map">
          ${layout.edges.map(renderMindMapEdge).join("")}
          ${layout.nodes.map(renderMindMapNode).join("")}
        </svg>
      </div>
    </div>
  `;
}

function renderMindMapEdge(edge) {
  return `
    <path class="mind-edge ${edge.type === "theme-link" ? "is-theme-link" : ""}" d="${edge.path}"></path>
  `;
}

function renderMindMapNode(node) {
  const lines = wrapMapLabel(node.label, node.role === "hub" ? 12 : 18, 2);
  const meta = truncateGraphLabel(node.meta || "", node.role === "theme" ? 20 : 24);
  const titleY = meta ? 24 : 30;
  const isActive = currentKnowledgeMapNodeId() === node.id;
  const classes = [
    "mind-node",
    `mind-node-${node.role}`,
    node.paperId || node.role === "theme" ? "is-interactive" : "",
    node.role === "theme" && !node.expanded ? "is-collapsed" : "",
    isActive ? "is-active" : ""
  ].filter(Boolean).join(" ");
  return `
    <g
      class="${classes}"
      transform="translate(${node.x.toFixed(1)} ${node.y.toFixed(1)})"
      data-node-id="${escapeHtml(node.id)}"
      data-node-role="${escapeHtml(node.role)}"
      ${node.paperId ? `data-paper-id="${escapeHtml(node.paperId)}"` : ""}
    >
      <title>${escapeHtml([node.label, node.meta, node.description].filter(Boolean).join(" · "))}</title>
      <rect width="${node.width}" height="${node.height}" rx="${node.role === "hub" ? 28 : 18}" ry="${node.role === "hub" ? 28 : 18}"></rect>
      ${renderSvgTextLines(lines, 18, titleY, 18, "mind-node-title")}
      ${meta ? `<text class="mind-node-meta" x="18" y="${node.height - 16}">${escapeXml(meta)}</text>` : ""}
      ${node.role === "theme" ? renderMindMapToggle(node) : ""}
    </g>
  `;
}

function renderMindMapToggle(node) {
  const centerX = node.width - 20;
  const centerY = 18;
  return `
    <g aria-hidden="true">
      <circle class="mind-node-toggle" cx="${centerX}" cy="${centerY}" r="10"></circle>
      <line class="mind-node-toggle-mark" x1="${centerX - 4}" y1="${centerY}" x2="${centerX + 4}" y2="${centerY}"></line>
      ${node.expanded ? "" : `<line class="mind-node-toggle-mark" x1="${centerX}" y1="${centerY - 4}" x2="${centerX}" y2="${centerY + 4}"></line>`}
    </g>
  `;
}

function renderKnowledgeGraphView(graph) {
  const layout = layoutKnowledgeGraph(graph);
  if (!layout.nodes.length) {
    return '<div class="map-empty"><div><h3>暂无图谱</h3><p>请先导入论文，或重新生成知识地图。</p></div></div>';
  }
  return `
    <div class="map-stage" data-map-stage>
      <div class="map-scene graph-shell" data-map-scene style="width:${layout.width}px; height:${layout.height}px;">
        <svg viewBox="0 0 ${layout.width} ${layout.height}" role="img" aria-label="Knowledge graph">
          ${layout.edges.map((edge) => {
            const midX = ((edge.source.x + edge.target.x) / 2).toFixed(1);
            const midY = ((edge.source.y + edge.target.y) / 2).toFixed(1);
            return `
              <g>
                <line class="graph-edge" x1="${edge.source.x.toFixed(1)}" y1="${edge.source.y.toFixed(1)}" x2="${edge.target.x.toFixed(1)}" y2="${edge.target.y.toFixed(1)}"></line>
                ${edge.label ? `<text class="graph-edge-label" x="${midX}" y="${midY}">${escapeHtml(truncateGraphLabel(edge.label, 14))}</text>` : ""}
              </g>
            `;
          }).join("")}
          ${layout.nodes.map((node) => `
            <g
              class="graph-node graph-node-${escapeHtml(node.type || "paper")} ${node.paperId ? "graph-node-clickable" : ""} ${currentKnowledgeMapNodeId() === node.id ? "is-active" : ""}"
              transform="translate(${node.x.toFixed(1)} ${node.y.toFixed(1)})"
              data-node-id="${escapeHtml(node.id)}"
              data-node-role="${escapeHtml(node.type || "paper")}"
              ${node.paperId ? `data-paper-id="${escapeHtml(node.paperId)}"` : ""}
            >
              <title>${escapeHtml([node.label, node.meta].filter(Boolean).join(" · "))}</title>
              <circle r="${Math.max(12, Number(node.size) || 14)}"></circle>
              <text y="4">${escapeHtml(truncateGraphLabel(node.label || "Node", 14))}</text>
              ${node.meta ? `<text class="graph-node-meta" y="${Math.max(18, (Number(node.size) || 14) + 14)}">${escapeHtml(truncateGraphLabel(node.meta, 18))}</text>` : ""}
            </g>
          `).join("")}
        </svg>
      </div>
    </div>
  `;
}

function layoutMindMap(mindMap) {
  const branches = Array.isArray(mindMap.children) ? mindMap.children : [];
  if (!branches.length) {
    return { width: 0, height: 0, nodes: [], edges: [] };
  }

  const width = 1760;
  const centerX = width / 2;
  const centerNode = {
    id: "hub",
    role: "hub",
    label: mindMap.label || "Paper Hub 论文知识地图",
    meta: "主题总览",
    description: "从当前论文库中抽取主题、关键概念和代表论文，形成动态阅读脉络。",
    width: 290,
    height: 92
  };
  const themeWidth = 250;
  const themeHeight = 78;
  const leafWidth = 230;
  const conceptHeight = 52;
  const paperHeight = 58;
  const branchGap = 28;
  const childGap = 14;

  const groups = branches.map((branch, index) => {
    const concepts = (Array.isArray(branch.children) ? branch.children : []).filter((child) => child.type === "concept");
    const papers = (Array.isArray(branch.children) ? branch.children : []).filter((child) => child.type !== "concept");
    const children = [...concepts, ...papers];
    const expanded = state.libraryMap.expandedThemes.has(branch.id);
    const childHeight = expanded
      ? children.reduce((sum, child, childIndex) => sum + (child.type === "concept" ? conceptHeight : paperHeight) + (childIndex ? childGap : 0), 0)
      : 0;
    const blockHeight = Math.max(themeHeight, childHeight);
    return {
      branch,
      children,
      expanded,
      side: index % 2 === 0 ? "right" : "left",
      blockHeight
    };
  });

  const leftGroups = groups.filter((item) => item.side === "left");
  const rightGroups = groups.filter((item) => item.side === "right");
  const leftHeight = leftGroups.reduce((sum, item, index) => sum + item.blockHeight + (index ? branchGap : 0), 0);
  const rightHeight = rightGroups.reduce((sum, item, index) => sum + item.blockHeight + (index ? branchGap : 0), 0);
  const height = Math.max(860, Math.max(leftHeight, rightHeight) + 240);
  const centerY = height / 2;

  const nodes = [];
  const edges = [];
  const hubX = centerX - centerNode.width / 2;
  const hubY = centerY - centerNode.height / 2;
  nodes.push({ ...centerNode, x: hubX, y: hubY, expanded: true });

  placeMindMapSide(rightGroups, centerY - rightHeight / 2);
  placeMindMapSide(leftGroups, centerY - leftHeight / 2);

  return { width, height, nodes, edges };

  function placeMindMapSide(items, startY) {
    let cursorY = startY;
    items.forEach((item) => {
      const branch = item.branch;
      const themeY = cursorY + item.blockHeight / 2 - themeHeight / 2;
      const themeX = centerX + (item.side === "right" ? 280 : -280) - themeWidth / 2;
      nodes.push({
        id: branch.id,
        role: "theme",
        label: branch.label || "未命名主题",
        meta: branch.meta || `${item.children.length} 个节点`,
        description: branch.summaryZh || "该主题下包含若干相关论文与概念。",
        x: themeX,
        y: themeY,
        width: themeWidth,
        height: themeHeight,
        expanded: item.expanded
      });
      edges.push({
        type: "theme-link",
        path: buildMindEdgePath(
          item.side === "right"
            ? { x: hubX + centerNode.width, y: centerY }
            : { x: hubX, y: centerY },
          item.side === "right"
            ? { x: themeX, y: themeY + themeHeight / 2 }
            : { x: themeX + themeWidth, y: themeY + themeHeight / 2 },
          item.side
        )
      });

      if (item.expanded && item.children.length) {
        const totalChildrenHeight = item.children.reduce(
          (sum, child, index) => sum + (child.type === "concept" ? conceptHeight : paperHeight) + (index ? childGap : 0),
          0
        );
        let childY = cursorY + item.blockHeight / 2 - totalChildrenHeight / 2;
        item.children.forEach((child) => {
          const nodeHeight = child.type === "concept" ? conceptHeight : paperHeight;
          const childX = centerX + (item.side === "right" ? 620 : -620) - leafWidth / 2;
          nodes.push({
            id: child.id,
            role: child.type === "concept" ? "concept" : "paper",
            label: child.label || "节点",
            meta: child.meta || "",
            description: child.type === "concept"
              ? `${branch.label || "主题"} 下的关键概念`
              : paperMapDescription(child.paperId, child.meta),
            paperId: child.paperId || "",
            x: childX,
            y: childY,
            width: leafWidth,
            height: nodeHeight,
            expanded: true
          });
          edges.push({
            type: "child-link",
            path: buildMindEdgePath(
              item.side === "right"
                ? { x: themeX + themeWidth, y: themeY + themeHeight / 2 }
                : { x: themeX, y: themeY + themeHeight / 2 },
              item.side === "right"
                ? { x: childX, y: childY + nodeHeight / 2 }
                : { x: childX + leafWidth, y: childY + nodeHeight / 2 },
              item.side
            )
          });
          childY += nodeHeight + childGap;
        });
      }

      cursorY += item.blockHeight + branchGap;
    });
  }
}

function layoutKnowledgeGraph(graph) {
  const width = 1520;
  const height = 1080;
  const center = { x: width / 2, y: height / 2 };
  const sourceNodes = Array.isArray(graph.nodes) ? graph.nodes : [];
  const sourceEdges = Array.isArray(graph.edges) ? graph.edges : [];
  const nodes = sourceNodes.map((node) => ({ ...node }));
  const byId = new Map(nodes.map((node) => [node.id, node]));
  if (!nodes.length) {
    return { width, height, nodes: [], edges: [] };
  }

  const hub = nodes.find((node) => node.type === "hub") || nodes[0];
  hub.x = center.x;
  hub.y = center.y;

  const themes = nodes.filter((node) => node.type === "theme");
  const concepts = nodes.filter((node) => node.type === "concept");
  const papers = nodes.filter((node) => node.type === "paper");
  const themeAngles = new Map();
  themes.forEach((theme, index) => {
    const angle = (-Math.PI / 2) + ((Math.PI * 2) * index / Math.max(1, themes.length));
    themeAngles.set(theme.id, angle);
    theme.x = center.x + Math.cos(angle) * 260;
    theme.y = center.y + Math.sin(angle) * 260;
  });

  const groupedConcepts = groupNodesBy(concepts, "group");
  groupedConcepts.forEach((items, groupId) => {
    const baseAngle = themeAngles.get(groupId) ?? (-Math.PI / 2);
    const spread = Math.min(Math.PI / 2, 0.34 + items.length * 0.1);
    items.forEach((node, index) => {
      const angle = items.length === 1
        ? baseAngle
        : baseAngle - spread / 2 + (spread * index / (items.length - 1));
      node.x = center.x + Math.cos(angle) * 430;
      node.y = center.y + Math.sin(angle) * 430;
    });
  });

  const groupedPapers = groupNodesBy(papers, "group");
  groupedPapers.forEach((items, groupId) => {
    const baseAngle = themeAngles.get(groupId) ?? (-Math.PI / 2);
    const spread = Math.min(Math.PI * 0.9, 0.42 + items.length * 0.12);
    items.forEach((node, index) => {
      const angle = items.length === 1
        ? baseAngle
        : baseAngle - spread / 2 + (spread * index / (items.length - 1));
      const radius = 630 + (index % 2) * 36;
      node.x = center.x + Math.cos(angle) * radius;
      node.y = center.y + Math.sin(angle) * radius;
    });
  });

  nodes.forEach((node) => {
    if (typeof node.x !== "number" || typeof node.y !== "number") {
      node.x = center.x;
      node.y = center.y;
    }
  });

  const edges = sourceEdges
    .map((edge) => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { ...edge, source, target };
    })
    .filter(Boolean);

  return { width, height, nodes, edges };
}

function groupNodesBy(nodes, key) {
  const grouped = new Map();
  nodes.forEach((node) => {
    const groupKey = node?.[key] || "__ungrouped__";
    const list = grouped.get(groupKey) || [];
    list.push(node);
    grouped.set(groupKey, list);
  });
  return grouped;
}

function truncateGraphLabel(text, maxLength) {
  const raw = normalizeString(text);
  if (raw.length <= maxLength) return raw;
  return `${raw.slice(0, maxLength - 1)}…`;
}

function setKnowledgeMapPayload(payload, resetViewport = false) {
  state.libraryMap.payload = payload;
  const themes = Array.isArray(payload?.mindMap?.children) ? payload.mindMap.children : [];
  state.libraryMap.expandedThemes = new Set(themes.map((item) => item.id).filter(Boolean));
  rebuildKnowledgeMapNodeIndex(payload);
  state.libraryMap.hoveredNodeId = "";
  state.libraryMap.activeNodeId = defaultKnowledgeMapNodeId(payload);
  if (resetViewport) {
    state.libraryMap.viewport = createLibraryMapViewport(state.libraryMap.view);
  }
}

function rebuildKnowledgeMapNodeIndex(payload) {
  const index = new Map();
  const stats = payload?.stats || {};
  index.set("hub", {
    id: "hub",
    role: "hub",
    label: payload?.mindMap?.label || "Paper Hub 论文知识地图",
    meta: `${stats.paperCount || 0} 篇论文 · ${stats.themeCount || 0} 个主题`,
    copy: payload?.summaryZh || "系统已根据当前论文库生成全库知识地图。",
    paperId: ""
  });

  (payload?.mindMap?.children || []).forEach((theme) => {
    index.set(theme.id, {
      id: theme.id,
      role: "theme",
      label: theme.label || "未命名主题",
      meta: theme.meta || `${(theme.children || []).length} 个节点`,
      copy: theme.summaryZh || "该主题下包含若干相关论文与概念。",
      paperId: ""
    });
    (theme.children || []).forEach((child) => {
      index.set(child.id, {
        id: child.id,
        role: child.type === "concept" ? "concept" : "paper",
        label: child.label || "节点",
        meta: child.meta || "",
        copy: child.type === "concept"
          ? `${theme.label || "该主题"} 下的关键概念。`
          : paperMapDescription(child.paperId, child.meta),
        paperId: child.paperId || ""
      });
    });
  });

  (payload?.knowledgeGraph?.nodes || []).forEach((node) => {
    if (index.has(node.id)) return;
    index.set(node.id, {
      id: node.id,
      role: node.type || "node",
      label: node.label || "Node",
      meta: node.meta || "",
      copy: node.meta || "图谱节点",
      paperId: node.paperId || ""
    });
  });

  state.libraryMap.nodeIndex = index;
}

function defaultKnowledgeMapNodeId(payload) {
  if (!payload) return "";
  if (payload.scope?.mode === "paper" && payload.scope?.paperId) {
    const paperNodeId = `paper:${payload.scope.paperId}`;
    if (state.libraryMap.nodeIndex.has(paperNodeId)) return paperNodeId;
  }
  return state.libraryMap.nodeIndex.has("hub") ? "hub" : [...state.libraryMap.nodeIndex.keys()][0] || "";
}

function currentKnowledgeMapNodeId() {
  return state.libraryMap.hoveredNodeId || state.libraryMap.activeNodeId || defaultKnowledgeMapNodeId(state.libraryMap.payload);
}

function currentKnowledgeMapNode() {
  const nodeId = currentKnowledgeMapNodeId();
  return nodeId ? state.libraryMap.nodeIndex.get(nodeId) || null : null;
}

function syncKnowledgeMapSelection() {
  const payload = state.libraryMap.payload;
  const node = currentKnowledgeMapNode();
  if (!payload || !node) {
    elements.mapSelectionTitle.textContent = "Paper Hub 论文知识地图";
    elements.mapSelectionMeta.textContent = "";
    elements.mapSelectionCopy.textContent = "在图中悬停或点击节点，可以查看主题、概念和论文之间的关系。";
    elements.mapSelectionAction.classList.add("hidden");
    return;
  }

  const roleText = {
    hub: "中心主题",
    theme: "研究主题",
    concept: "关键概念",
    paper: "论文节点"
  }[node.role] || "图谱节点";

  elements.mapSelectionTitle.textContent = node.label || "知识地图节点";
  elements.mapSelectionMeta.textContent = [roleText, node.meta].filter(Boolean).join(" · ");
  elements.mapSelectionCopy.textContent = node.copy || payload.summaryZh || "图中节点可用于探索主题、概念和论文之间的关系。";
  if (node.paperId) {
    const paper = state.papers.find((item) => item.id === node.paperId);
    elements.mapSelectionAction.textContent = paper ? `定位论文：${truncateGraphLabel(paper.titleZh || paper.title, 18)}` : "定位论文";
    elements.mapSelectionAction.classList.remove("hidden");
  } else {
    elements.mapSelectionAction.classList.add("hidden");
  }
}

function syncKnowledgeMapViewport() {
  const scene = elements.mapCanvas.querySelector("[data-map-scene]");
  const stage = elements.mapCanvas.querySelector("[data-map-stage]");
  if (!scene || !stage) return;
  const { x, y, scale, panning } = state.libraryMap.viewport;
  scene.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
  stage.classList.toggle("is-panning", Boolean(panning));
}

function zoomKnowledgeMap(delta, clientX = null, clientY = null) {
  const stage = elements.mapCanvas.querySelector("[data-map-stage]");
  if (!stage) return;
  const current = state.libraryMap.viewport;
  const nextScale = Math.min(current.maxScale, Math.max(current.minScale, current.scale + delta));
  if (nextScale === current.scale) return;
  const bounds = stage.getBoundingClientRect();
  const originX = clientX == null ? bounds.left + bounds.width / 2 : clientX;
  const originY = clientY == null ? bounds.top + bounds.height / 2 : clientY;
  const localX = originX - bounds.left;
  const localY = originY - bounds.top;
  const worldX = (localX - current.x) / current.scale;
  const worldY = (localY - current.y) / current.scale;
  current.scale = Number(nextScale.toFixed(2));
  current.x = localX - worldX * current.scale;
  current.y = localY - worldY * current.scale;
  syncKnowledgeMapViewport();
}

function resetKnowledgeMapViewport(forceRender = false) {
  state.libraryMap.viewport = createLibraryMapViewport(state.libraryMap.view);
  if (forceRender) {
    renderKnowledgeMap();
    return;
  }
  syncKnowledgeMapViewport();
}

function releaseKnowledgeMapPointer() {
  state.libraryMap.viewport.panning = false;
  state.libraryMap.viewport.pointerId = null;
  syncKnowledgeMapViewport();
}

function toggleMindMapTheme(themeId) {
  if (!themeId) return;
  if (state.libraryMap.expandedThemes.has(themeId)) {
    state.libraryMap.expandedThemes.delete(themeId);
  } else {
    state.libraryMap.expandedThemes.add(themeId);
  }
  state.libraryMap.activeNodeId = themeId;
  renderKnowledgeMap();
}

function setAllMindMapThemesExpanded(expanded) {
  if (state.libraryMap.view !== "mind" || !state.libraryMap.payload) return;
  const themeIds = (state.libraryMap.payload.mindMap?.children || []).map((item) => item.id).filter(Boolean);
  state.libraryMap.expandedThemes = expanded ? new Set(themeIds) : new Set();
  renderKnowledgeMap();
}

function openActiveKnowledgeMapPaper() {
  const node = currentKnowledgeMapNode();
  if (!node?.paperId) return;
  openPaperFromKnowledgeMap(node.paperId);
}

function openPaperFromKnowledgeMap(paperId) {
  if (!paperId) return;
  const paper = state.papers.find((item) => item.id === paperId);
  if (!paper) return;
  state.selectedPaperId = paperId;
  render();
  closeKnowledgeMapDialog();
  setNotice(`已定位到论文：${paper.title}`);
}

function buildMindEdgePath(source, target, side) {
  const direction = side === "right" ? 1 : -1;
  const delta = Math.abs(target.x - source.x);
  const control = Math.max(80, delta * 0.42);
  return [
    `M ${source.x.toFixed(1)} ${source.y.toFixed(1)}`,
    `C ${(source.x + control * direction).toFixed(1)} ${source.y.toFixed(1)},`,
    `${(target.x - control * direction).toFixed(1)} ${target.y.toFixed(1)},`,
    `${target.x.toFixed(1)} ${target.y.toFixed(1)}`
  ].join(" ");
}

function wrapMapLabel(text, maxChars = 16, maxLines = 2) {
  const raw = normalizeString(text);
  if (!raw) return [""];
  const tokens = /\s/.test(raw) ? raw.split(/\s+/) : raw.split("");
  const lines = [];
  let current = "";
  tokens.forEach((token) => {
    const joiner = /\s/.test(raw) && current ? " " : "";
    const next = `${current}${joiner}${token}`;
    if (next.length <= maxChars || !current) {
      current = next;
      return;
    }
    lines.push(current);
    current = token;
  });
  if (current) lines.push(current);
  if (lines.length <= maxLines) return lines;
  return [...lines.slice(0, maxLines - 1), truncateGraphLabel(lines.slice(maxLines - 1).join(" "), maxChars)];
}

function renderSvgTextLines(lines, x, y, lineHeight, className) {
  return `
    <text class="${className}" x="${x}" y="${y}">
      ${lines.map((line, index) => `<tspan x="${x}" dy="${index === 0 ? 0 : lineHeight}">${escapeXml(line)}</tspan>`).join("")}
    </text>
  `;
}

function paperMapDescription(paperId, fallbackMeta = "") {
  const paper = state.papers.find((item) => item.id === paperId);
  if (!paper) return fallbackMeta || "论文节点";
  return truncateGraphLabel(
    paper.aiSummaryZh || paper.aiSummary || paper.abstract || paper.notes || fallbackMeta || "论文节点",
    220
  );
}

function handleProviderSelectionChange() {
  if (!state.providerConfig) return;
  state.providerConfig.selectedProvider = elements.providerSelect.value;
  renderProviderDialog();
}

function renderProviderDialog() {
  if (!state.providerConfig) return;
  const presets = Array.isArray(state.providerConfig.presets) ? state.providerConfig.presets : [];
  const selectedProvider = state.providerConfig.selectedProvider || presets[0]?.id || "openai";
  const providerMap = state.providerConfig.providers || {};
  const preset = presets.find((item) => item.id === selectedProvider) || null;
  const provider = providerMap[selectedProvider] || {};

  elements.providerSelect.innerHTML = presets.map((item) => `
    <option value="${escapeHtml(item.id)}" ${item.id === selectedProvider ? "selected" : ""}>${escapeHtml(item.label)}</option>
  `).join("");

  elements.providerLabel.textContent = preset?.label || selectedProvider;
  elements.providerDescription.textContent = preset?.description || "";
  elements.providerCapabilities.innerHTML = [
    selectedProvider === "relay-openai" ? "中转站接入" : "",
    preset?.supportsVision ? "支持视觉翻译" : "仅文本翻译",
    preset?.requiresApiKey ? "需要 API Key" : "无需 API Key",
    preset?.protocol ? `协议: ${preset.protocol}` : ""
  ]
    .filter(Boolean)
    .map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`)
    .join("");

  elements.providerModel.value = provider.model || preset?.defaultModel || "";
  elements.providerApiUrl.value = provider.apiUrl || preset?.defaultApiUrl || "";
  elements.providerApiKey.value = "";
  elements.providerClearApiKey.checked = false;
  const keyStatus = provider.hasApiKey
    ? `当前已保存 Key: ${provider.apiKeyMasked || "已保存"}`
    : "当前还没有保存 API Key。";
  const relayHint = selectedProvider === "relay-openai"
    ? "中转站填写方式：API URL 填完整的 /v1/chat/completions 地址，Model 填中转站提供的模型名。若中转站支持视觉模型，就可直接用于嵌入翻译。"
    : "";
  elements.providerKeyHint.textContent = [keyStatus, relayHint].filter(Boolean).join(" ");
}

async function saveProviderConfig() {
  if (!state.providerConfig) return;
  const selectedProvider = elements.providerSelect.value;
  const payload = await api("/api/provider-config", {
    method: "PUT",
    body: JSON.stringify({
      selectedProvider,
      provider: {
        model: normalizeString(elements.providerModel.value),
        apiUrl: normalizeString(elements.providerApiUrl.value),
        apiKey: normalizeString(elements.providerApiKey.value),
        clearApiKey: elements.providerClearApiKey.checked
      }
    })
  });
  state.providerConfig = payload.config;
  state.config = payload.appConfig;
  closeProviderDialog();
  render();
  setNotice(`已切换 AI Provider: ${state.config.aiProviderLabel || state.config.aiProvider}`);
}

async function openReader(paper) {
  if (!paper.pdfPath) {
    setNotice("这篇论文没有本地 PDF，暂时不能在应用内阅读。");
    return;
  }

  const reader = await api(`/api/papers/${paper.id}/reader`);
  state.reader.paperId = paper.id;
  state.reader.pages = reader.pages || [];
  state.reader.currentPage = reader.currentPage || 1;
  state.reader.mode = state.config.aiEnabled ? "translated" : "original";
  state.reader.translations = {};
  state.reader.loadingPages = new Set();
  elements.readerTitle.textContent = paper.titleZh || paper.title;
  elements.readerSourceLink.href = reader.pdfUrl || "#";
  renderReaderPages();
  renderReaderModeButtons();
  updateReaderMeta();
  elements.readerDialog.showModal();
  requestAnimationFrame(() => {
    scrollReaderToPage(state.reader.currentPage, false);
    if (state.reader.mode !== "original") {
      ensureReaderTranslation(state.reader.currentPage);
      ensureReaderTranslation(state.reader.currentPage + 1);
    }
  });
}

function renderReaderPages() {
  if (state.reader.observer) {
    state.reader.observer.disconnect();
  }
  elements.readerScroll.innerHTML = "";
  state.reader.pages.forEach((page) => {
    const article = document.createElement("article");
    article.className = "reader-page";
    article.dataset.page = String(page.page);
    article.innerHTML = `
      <div class="reader-page-sensor" data-page-sensor="${page.page}" aria-hidden="true"></div>
      <div class="reader-page-head">第 ${page.page} 页</div>
      <div class="reader-page-frame">
        <img src="${page.imageUrl}" alt="PDF page ${page.page}" loading="lazy">
        <div class="reader-translation-holder"></div>
      </div>
      <div class="reader-clean-panel"></div>
    `;
    elements.readerScroll.append(article);
  });

  state.reader.observer = new IntersectionObserver(handleReaderIntersection, {
    root: elements.readerScroll,
    threshold: 0,
    rootMargin: "-18% 0px -72% 0px"
  });
  elements.readerScroll.querySelectorAll(".reader-page-sensor").forEach((node) => {
    state.reader.observer.observe(node);
  });
  renderReaderCleanPanels();
  renderReaderTranslationLayers();
}

function handleReaderIntersection(entries) {
  const visible = entries
    .filter((entry) => entry.isIntersecting)
    .sort((left, right) => Number(left.target.dataset.pageSensor) - Number(right.target.dataset.pageSensor));
  if (!visible[0]) return;
  const page = Number(visible[0].target.dataset.pageSensor);
  if (!page || page === state.reader.currentPage) return;
  state.reader.currentPage = page;
  updateReaderMeta();
  if (state.reader.mode !== "original") {
    ensureReaderTranslation(page);
    ensureReaderTranslation(page + 1);
  }
  scheduleReaderStateSave();
}

function scrollReaderToPage(page, smooth = true) {
  const node = elements.readerScroll.querySelector(`[data-page="${page}"]`);
  if (!node) return;
  node.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
  state.reader.currentPage = page;
  updateReaderMeta();
  if (state.reader.mode !== "original") {
    ensureReaderTranslation(page);
    ensureReaderTranslation(page + 1);
  }
  scheduleReaderStateSave();
}

function updateReaderMeta() {
  const total = state.reader.pages.length;
  const modeLabel = state.reader.mode === "translated"
    ? "中文精读"
    : state.reader.mode === "embedded"
      ? "嵌入翻译"
      : "原文";
  elements.readerMeta.textContent = total ? `${state.reader.currentPage} / ${total} · ${modeLabel}` : modeLabel;
}

function renderReaderModeButtons() {
  elements.readerOriginalButton.classList.toggle("active", state.reader.mode === "original");
  elements.readerTranslatedButton.classList.toggle("active", state.reader.mode === "translated");
  elements.readerEmbeddedButton.classList.toggle("active", state.reader.mode === "embedded");
  const job = state.reader.translationJob;
  const running = job && (job.status === "running" || job.status === "queued");
  elements.readerPretranslateButton.disabled = !state.config.aiEnabled || !state.reader.paperId || running;
  if (running) {
    elements.readerPretranslateButton.textContent = `翻译中 ${job.completedPages}/${job.totalPages}`;
  } else {
    elements.readerPretranslateButton.textContent = "一键全文翻译";
  }
  elements.readerEmbeddedButton.disabled = !state.config.aiEnabled || !state.config.supportsVisionTranslation || !state.reader.paperId;
  updateReaderMeta();
  renderReaderProgress();
  renderReaderCleanPanels();
  renderReaderTranslationLayers();
}

function setReaderMode(mode) {
  if (mode === "embedded" && !state.config.supportsVisionTranslation) {
    setNotice(`${state.config.aiProviderLabel || state.config.aiProvider} does not support vision translation in the current setup. Use 中文精读 or switch to a vision-capable provider.`);
    return;
  }
  state.reader.mode = mode;
  renderReaderModeButtons();
  if (mode !== "original") {
    ensureReaderTranslation(state.reader.currentPage);
    ensureReaderTranslation(state.reader.currentPage + 1);
  }
}

async function ensureReaderTranslation(pageNumber) {
  if (state.reader.mode === "original") return;
  if (!state.reader.paperId) return;
  if (!Number.isInteger(pageNumber) || pageNumber < 1 || pageNumber > state.reader.pages.length) return;
  if (state.reader.translations[pageNumber] || state.reader.loadingPages.has(pageNumber)) return;

  state.reader.loadingPages.add(pageNumber);
  try {
    const payload = await api(`/api/papers/${state.reader.paperId}/reader-translation?page=${pageNumber}`);
    state.reader.translations[pageNumber] = payload;
    renderReaderCleanPanels();
    renderReaderTranslationLayers();
  } catch (error) {
    if (state.reader.mode !== "original") {
      state.reader.mode = "original";
      renderReaderModeButtons();
      setNotice(`中文阅读暂时不可用：${error.message}`);
    }
  } finally {
    state.reader.loadingPages.delete(pageNumber);
  }
}

async function refreshReaderTranslations() {
  if (!state.reader.paperId) return;
  const bulk = await api(`/api/papers/${state.reader.paperId}/reader-translations`);
  const translations = {};
  for (const item of (bulk.pages || [])) {
    if (item && Number.isInteger(item.page)) {
      translations[item.page] = item;
    }
  }
  state.reader.translations = translations;
  state.reader.translationLoadedPages = Object.keys(translations).length;
  renderReaderModeButtons();
}

function stopReaderTranslationJobPolling() {
  window.clearInterval(state.reader.translationJobTimer);
  state.reader.translationJobTimer = null;
}

async function pollReaderTranslationJob() {
  if (!state.reader.paperId) return;
  try {
    const job = await api(`/api/papers/${state.reader.paperId}/reader-translation-job`);
    state.reader.translationJob = job;
    if ((job.completedPages || 0) !== state.reader.translationLoadedPages || (job.status && job.status !== "idle")) {
      await refreshReaderTranslations();
    } else {
      renderReaderModeButtons();
    }
    if (job.status === "completed" || job.status === "completed_with_errors" || job.status === "failed") {
      stopReaderTranslationJobPolling();
      if (job.completedPages > 0) {
        state.reader.mode = "translated";
      }
      renderReaderModeButtons();
      const suffix = job.status === "completed_with_errors" ? `，失败页：${(job.failedPages || []).join(", ")}` : "";
      const message = job.message ? `。${job.message}` : "";
      setNotice(`全文翻译完成：${job.completedPages}/${job.totalPages} 页${suffix}${message}`);
    }
  } catch (error) {
    stopReaderTranslationJobPolling();
    showError(error);
  }
}

function renderReaderProgress() {
  const job = state.reader.translationJob;
  if (!job || !job.totalPages) {
    elements.readerProgress.innerHTML = "";
    elements.readerProgress.classList.add("hidden");
    return;
  }
  const completed = Number(job.completedPages || 0);
  const failed = Array.isArray(job.failedPages) ? job.failedPages.length : 0;
  const running = Array.isArray(job.runningPages) ? job.runningPages.length : 0;
  const total = Number(job.totalPages || 0);
  const percent = total > 0 ? Math.max(0, Math.min(100, Math.round((completed / total) * 100))) : 0;
  const summary = [
    `已完成 ${completed}/${total}`,
    running ? `进行中 ${running}` : "",
    failed ? `失败 ${failed}` : ""
  ].filter(Boolean).join(" · ");
  elements.readerProgress.classList.remove("hidden");
  const chips = Array.from({ length: job.totalPages }, (_, index) => {
    const page = index + 1;
    const status = job.pageStatus?.[String(page)] || "pending";
    return `<span class="reader-progress-chip ${escapeHtml(status)}" title="第 ${page} 页 ${escapeHtml(status)}">${page}</span>`;
  }).join("");
  elements.readerProgress.innerHTML = `
    <div class="reader-progress-summary">
      <div class="reader-progress-copy">
        <strong>全文翻译进度 ${percent}%</strong>
        <span>${escapeHtml(summary)}</span>
      </div>
      <div class="reader-progress-bar" aria-hidden="true">
        <span style="width:${percent}%"></span>
      </div>
    </div>
    <div class="reader-progress-grid">${chips}</div>
  `;
}

async function preloadReaderTranslation() {
  if (!state.reader.paperId) return;
  try {
    const job = await api(`/api/papers/${state.reader.paperId}/reader-translation-job`, {
      method: "POST",
      body: JSON.stringify({})
    });
    state.reader.translationJob = job;
    renderReaderModeButtons();
    await refreshReaderTranslations();
    stopReaderTranslationJobPolling();
    state.reader.translationJobTimer = window.setInterval(pollReaderTranslationJob, 1200);
    setNotice(`已启动全文翻译任务：${job.completedPages}/${job.totalPages} 页`);
  } catch (error) {
    showError(error);
  }
}

function renderReaderTranslationLayers() {
  elements.readerScroll.querySelectorAll(".reader-page").forEach((node) => {
    const pageNumber = Number(node.dataset.page);
    const holder = node.querySelector(".reader-translation-holder");
    if (!holder) return;
    const translation = state.reader.translations[pageNumber];
    const shouldShow = state.reader.mode === "embedded" && translation;
    node.classList.toggle("embedded-mode", Boolean(shouldShow));
    if (!shouldShow) {
      holder.innerHTML = "";
      return;
    }
    holder.innerHTML = buildReaderTranslationSvg(translation);
  });
}

function renderReaderCleanPanels() {
  elements.readerScroll.querySelectorAll(".reader-page").forEach((node) => {
    const pageNumber = Number(node.dataset.page);
    const panel = node.querySelector(".reader-clean-panel");
    if (!panel) return;
    const translation = state.reader.translations[pageNumber];
    const shouldShow = state.reader.mode === "translated";
    node.classList.toggle("clean-mode", shouldShow);
    if (!shouldShow) {
      panel.innerHTML = "";
      return;
    }
    if (!translation) {
      panel.innerHTML = '<p class="reader-clean-empty">正在生成这一页的中文精读内容...</p>';
      return;
    }
    const paragraphs = buildReaderParagraphs(translation);
    panel.innerHTML = paragraphs.length
      ? `<h4>第 ${pageNumber} 页中文精读</h4>${paragraphs.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}`
      : '<p class="reader-clean-empty">这一页没有可提取的文字内容。</p>';
  });
}

function buildReaderParagraphs(translation) {
  const blocks = Array.isArray(translation.blocks) ? translation.blocks : [];
  return blocks
    .map((block) => normalizeString(block.text))
    .filter(Boolean)
    .reduce((result, item) => {
      const last = result[result.length - 1] || "";
      if (last && `${last} ${item}`.length < 180) {
        result[result.length - 1] = `${last} ${item}`;
      } else {
        result.push(item);
      }
      return result;
    }, []);
}

function exportLibrary() {
  const blob = new Blob([JSON.stringify(state.papers, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "paper-hub-library.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

async function resetDatabase() {
  if (!confirm("用示例数据重置数据库？")) return;
  await api("/api/reset", { method: "POST" });
  state.selectedPaperId = null;
  state.activeTag = "all";
  state.view = "grid";
  state.filters = {
    search: "",
    status: "all",
    collection: "all",
    favoritesOnly: false,
    sort: "recent"
  };
  elements.searchInput.value = "";
  elements.statusFilter.value = "all";
  elements.sortFilter.value = "recent";
  elements.favoriteFilter.checked = false;
  await refreshPapers();
}

function getVisiblePapers() {
  const search = state.filters.search.toLowerCase();
  return [...state.papers]
    .filter((paper) => {
      const matchesStatus = state.filters.status === "all" || paper.status === state.filters.status;
      const matchesCollection = state.filters.collection === "all" || paper.collection === state.filters.collection;
      const matchesFavorite = !state.filters.favoritesOnly || paper.favorite;
      const matchesTag = state.activeTag === "all" || (paper.tags || []).includes(state.activeTag);
      const haystack = [
        paper.title,
        (paper.authors || []).join(" "),
        (paper.tags || []).join(" "),
        paper.abstract,
        paper.venue,
        paper.notes,
        paper.collection,
        paper.originalFilename || ""
      ].join(" ").toLowerCase();
      return matchesStatus && matchesCollection && matchesFavorite && matchesTag && (!search || haystack.includes(search));
    })
    .sort((left, right) => {
      switch (state.filters.sort) {
        case "rating":
          return (right.rating || 0) - (left.rating || 0);
        case "year":
          return (right.year || 0) - (left.year || 0);
        case "priority":
          return priorityScore(right.priority) - priorityScore(left.priority);
        case "favorite":
          return Number(right.favorite) - Number(left.favorite);
        case "recent":
        default:
          return new Date(right.updatedAt) - new Date(left.updatedAt);
      }
    });
}

function getSelectedPaper() {
  return state.papers.find((paper) => paper.id === state.selectedPaperId) || null;
}

function setView(nextView) {
  state.view = nextView;
  render();
}

function createLibraryMapViewport(view = "mind") {
  return {
    scale: view === "graph" ? 0.84 : 0.9,
    x: view === "graph" ? 110 : 64,
    y: view === "graph" ? 62 : 74,
    minScale: 0.45,
    maxScale: 1.8,
    panning: false,
    pointerId: null,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0
  };
}

function priorityScore(priority) {
  if (priority === "high") return 3;
  if (priority === "medium") return 2;
  return 1;
}

function setValue(id, value) {
  const element = document.querySelector(`#${id}`);
  if (element) element.value = value;
}

function parseCommaSeparated(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function normalizeString(value) {
  return String(value || "").trim();
}

function normalizeNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : 0;
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function updateCoverPreview() {
  const previewPaper = {
    title: normalizeString(document.querySelector("#paperTitle")?.value) || "New Paper",
    year: normalizeNumber(document.querySelector("#paperYear")?.value),
    coverImage: state.draftCoverImage
  };
  applyCoverPresentation(elements.coverPreview, previewPaper, "preview");
}

function applyCoverPresentation(element, paper, variant) {
  const coverImage = paper.coverImage || "";
  element.classList.remove("placeholder");
  element.textContent = "";
  if (coverImage) {
    element.style.backgroundImage = `linear-gradient(180deg, rgba(19, 31, 27, 0.02), rgba(19, 31, 27, 0.14)), url("${coverImage}")`;
    return;
  }
  element.style.backgroundImage = gradientFromPaper(paper);
  element.classList.add("placeholder");
  element.textContent = formatPlaceholderLabel(paper.title, paper.year);
  if (variant === "card") element.textContent = "";
}

function gradientFromPaper(paper) {
  const text = `${paper.title || ""}${paper.year || ""}`;
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = text.charCodeAt(index) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  const secondaryHue = (hue + 54) % 360;
  return `linear-gradient(135deg, hsl(${hue} 44% 32%), hsl(${secondaryHue} 48% 48%))`;
}

function formatPlaceholderLabel(title, year) {
  const words = String(title || "Paper").split(/\s+/).slice(0, 4).join(" ");
  return `${words}\n${year || ""}`.trim();
}

async function api(url, options = {}) {
  const init = {
    method: options.method || "GET",
    body: options.body,
    headers: options.isForm ? {} : { "Content-Type": "application/json", ...(options.headers || {}) }
  };
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    let message = text || `HTTP ${response.status}`;
    try {
      const payload = JSON.parse(text);
      message = payload.error || payload.message || message;
    } catch {}
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function showError(error) {
  console.error(error);
  setNotice(`应用没有正常连上本地服务：${error.message}`);
  alert(`出错了：${error.message}`);
}

function setNotice(message) {
  if (!elements.appNotice) return;
  elements.appNotice.classList.remove("hidden");
  elements.appNotice.innerHTML = `<strong>运行提示</strong><span>${escapeHtml(message)}</span>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeXml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

