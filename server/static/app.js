/**
 * app.js — Giao diện Chat kiểu Gemini cho Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải
 */

document.addEventListener('DOMContentLoaded', () => {
  // ============================================================================
  // BẢO MẬT: TỰ ĐỘNG GẮN AUTH TOKEN CHO TẤT CẢ CÁC YÊU CẦU /api/*
  // ============================================================================
  const _rawFetch = window.fetch;
  window.fetch = function(url, options = {}) {
    const token = localStorage.getItem('cva_auth_token') || '';
    if (token && typeof url === 'string' && url.startsWith('/api/')) {
      const opts = Object.assign({}, options);
      opts.headers = Object.assign({}, opts.headers || {});
      if (!opts.headers['Authorization'] && !opts.headers['authorization']) {
        opts.headers['Authorization'] = `Bearer ${token}`;
      }
      return _rawFetch.call(this, url, opts);
    }
    return _rawFetch.call(this, url, options);
  };

  // Trạng thái phiên làm việc (Chế độ Khách lưu sessionStorage, Cán bộ đăng nhập lưu localStorage)
  function getStoredSessionId() {
    const token = localStorage.getItem('cva_auth_token');
    if (token) return localStorage.getItem('cva_session_id') || '';
    return sessionStorage.getItem('cva_guest_session_id') || '';
  }

  function saveSessionId(sid) {
    sessionId = sid;
    const token = localStorage.getItem('cva_auth_token');
    if (token) {
      localStorage.setItem('cva_session_id', sid);
    } else {
      sessionStorage.setItem('cva_guest_session_id', sid);
    }
  }

  let sessionId = getStoredSessionId();
  let pendingAttachments = []; // [{ id, name, category_label, char_count }]
  let isSending = false;
  let lastUserPrompt = '';

  // ============================================================================
  // HỆ THỐNG TOAST THÔNG BÁO HIỆN ĐẠI (THAY THẾ TOÀN BỘ ALERT TRÌNH DUYỆT)
  // ============================================================================
  function showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : (type === 'warning' ? '⚠' : 'ℹ'));
    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-msg">${escapeHtml(message)}</span>
      <button class="toast-close" type="button">✕</button>
    `;
    container.appendChild(toast);
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.classList.add('hide');
      setTimeout(() => toast.remove(), 250);
    });
    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 250);
      }
    }, duration);
  }

  // ============================================================================
  // CHẾ ĐỘ BAN ĐÊM (DARK THEME / EYE-CARE MODE)
  // ============================================================================
  function initTheme() {
    const savedTheme = localStorage.getItem('chs_theme') || 'light';
    const icon = document.getElementById('themeToggleIcon');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
      if (icon) icon.textContent = '☀️';
    } else {
      document.body.classList.remove('dark-theme');
      if (icon) icon.textContent = '🌙';
    }
  }
  initTheme();

  const btnThemeToggle = document.getElementById('btnThemeToggle');
  if (btnThemeToggle) {
    btnThemeToggle.addEventListener('click', () => {
      const isDark = document.body.classList.toggle('dark-theme');
      localStorage.setItem('chs_theme', isDark ? 'dark' : 'light');
      const icon = document.getElementById('themeToggleIcon');
      if (icon) icon.textContent = isDark ? '☀️' : '🌙';
      showToast(isDark ? '🌙 Đã bật chế độ Ban đêm dịu mắt' : '☀️ Đã bật chế độ Sáng tiêu chuẩn', 'info', 2000);
    });
  }

  // DOM Elements
  const aiStatus = document.getElementById('aiStatus');
  const aiStatusText = document.getElementById('aiStatusText');
  const btnNewChat = document.getElementById('btnNewChat');
  const chatScroll = document.getElementById('chatScroll');
  const welcome = document.getElementById('welcome');
  const messagesContainer = document.getElementById('messages');
  const composer = document.getElementById('composer');
  const attachList = document.getElementById('attachList');
  const input = document.getElementById('input');
  const btnAttach = document.getElementById('btnAttach');
  const btnSend = document.getElementById('btnSend');
  const fileInput = document.getElementById('fileInput');
  const dropOverlay = document.getElementById('dropOverlay');
  const topbarModelName = document.getElementById('topbarModelName');

  // DOM Sidebar
  const btnToggleSidebar = document.getElementById('btnToggleSidebar');
  const chatSidebar = document.getElementById('chatSidebar');
  const btnCloseSidebarMobile = document.getElementById('btnCloseSidebarMobile');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const btnNewChatSidebar = document.getElementById('btnNewChatSidebar');
  const sidebarSessionsList = document.getElementById('sidebarSessionsList');
  const inputSearchSessionsSidebar = document.getElementById('inputSearchSessionsSidebar');

  function closeMobileSidebar() {
    if (chatSidebar) chatSidebar.classList.remove('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
  }

  if (btnToggleSidebar && chatSidebar) {
    btnToggleSidebar.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        const isOpen = chatSidebar.classList.toggle('mobile-open');
        if (sidebarBackdrop) sidebarBackdrop.classList.toggle('active', isOpen);
      } else {
        chatSidebar.classList.toggle('collapsed');
      }
    });
  }

  if (btnCloseSidebarMobile) btnCloseSidebarMobile.addEventListener('click', closeMobileSidebar);
  if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeMobileSidebar);

  if (btnNewChatSidebar) {
    btnNewChatSidebar.addEventListener('click', () => {
      if (btnNewChat) btnNewChat.click();
      closeMobileSidebar();
    });
  }

  // Modal xem nhanh các Dự thảo Word gần đây
  const btnQuickRecentDocs = document.getElementById('btnQuickRecentDocs');
  const modalRecentDocs = document.getElementById('modalRecentDocs');
  const btnCloseRecentDocsModal = document.getElementById('btnCloseRecentDocsModal');
  const btnCancelRecentDocsModal = document.getElementById('btnCancelRecentDocsModal');
  const recentDocsList = document.getElementById('recentDocsList');

  async function openRecentDocsModal() {
    if (!modalRecentDocs || !recentDocsList) return;
    modalRecentDocs.style.display = 'flex';
    recentDocsList.innerHTML = '<div style="text-align:center; padding:25px; color:var(--text-muted);">⏳ Đang quét danh sách văn bản dự thảo gần đây...</div>';

    try {
      const res = await fetch('/api/chat/recent');
      if (!res.ok) throw new Error('Không thể tải danh sách tệp');
      const data = await res.json();
      const files = data.files || [];

      if (files.length === 0) {
        recentDocsList.innerHTML = '<div style="text-align:center; padding:25px; color:var(--text-muted);">Chưa có văn bản dự thảo nào được tạo trong năm 2026.</div>';
        return;
      }

      recentDocsList.innerHTML = files.map((f) => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:22px;">📄</span>
            <div>
              <div style="font-weight:700; font-size:13.5px; color:var(--text-main);">${escapeHtml(f.name)}</div>
              <div style="font-size:11.5px; color:var(--text-muted);">${escapeHtml(f.category || 'Văn bản')} • ${f.size_kb ? f.size_kb + ' KB' : ''} • ${escapeHtml(f.modified || '')}</div>
            </div>
          </div>
          <a href="${escapeHtml(f.download_url)}" target="_blank" download class="btn-chs-outline" style="padding:6px 14px; font-size:12px; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">
            <span>⬇ Tải Word</span>
          </a>
        </div>
      `).join('');
    } catch (err) {
      recentDocsList.innerHTML = `<div style="color:#ef4444; padding:20px; text-align:center;">Lỗi: ${escapeHtml(err.message)}</div>`;
    }
  }

  if (btnQuickRecentDocs) btnQuickRecentDocs.addEventListener('click', openRecentDocsModal);
  if (btnCloseRecentDocsModal) btnCloseRecentDocsModal.addEventListener('click', () => modalRecentDocs.style.display = 'none');
  if (btnCancelRecentDocsModal) btnCancelRecentDocsModal.addEventListener('click', () => modalRecentDocs.style.display = 'none');

  // ============================================================================
  // TẢI & QUẢN LÝ LỊCH SỬ PHIÊN HỘI THOẠI TRÊN SIDEBAR
  // ============================================================================
  let allSidebarSessions = [];

  async function loadSidebarSessions() {
    if (!sidebarSessionsList) return;
    try {
      const res = await fetch('/api/admin/sessions?page=1&page_size=25');
      if (res.status === 401 || res.status === 403) {
        sidebarSessionsList.innerHTML = `
          <div style="font-size:12px; color:var(--text-muted); padding:16px; text-align:center;">
            Chế độ Khách (Phiên tạm thời).<br>
            <small style="opacity:0.8;">Đăng nhập để lưu lịch sử công tác</small>
          </div>
        `;
        return;
      }
      if (!res.ok) throw new Error('Không thể tải phiên');
      const data = await res.json();
      allSidebarSessions = data.sessions || [];
      renderSidebarSessions(allSidebarSessions);
    } catch {
      sidebarSessionsList.innerHTML = `
        <div style="font-size:12px; color:var(--text-muted); padding:16px; text-align:center;">
          Chưa có phiên làm việc trước đây.<br>
          <small style="opacity:0.8;">Bắt đầu trò chuyện để lưu nhật ký</small>
        </div>
      `;
    }
  }

  function renderSidebarSessions(sessions) {
    if (!sidebarSessionsList) return;
    if (!sessions || sessions.length === 0) {
      sidebarSessionsList.innerHTML = '<div style="font-size:12px; color:var(--text-muted); padding:16px; text-align:center;">Không tìm thấy phiên làm việc phù hợp.</div>';
      return;
    }

    sidebarSessionsList.innerHTML = sessions.map((s) => {
      const isCurrent = s.session_id === sessionId;
      const isZalo = s.channel === 'zalo' || String(s.session_id).startsWith('zalo_');
      const channelIcon = isZalo ? '💬' : '🌐';
      const title = s.last_user_message || s.first_user_message || 'Phiên làm việc';
      const time = (s.last_activity || '').substring(0, 10);

      return `
        <div class="sidebar-session-item ${isCurrent ? 'active' : ''}" data-sid="${escapeHtml(s.session_id)}">
          <div class="session-item-row">
            <span class="session-item-title" title="${escapeHtml(title)}">${channelIcon} ${escapeHtml(title)}</span>
            <button class="btn-delete-session" title="Xoá lịch sử phiên này" onclick="event.stopPropagation(); window.deleteSidebarSession('${escapeHtml(s.session_id)}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
          <div class="session-item-meta">
            <span>${escapeHtml(time)}</span>
            <span>•</span>
            <span>${s.total_messages || 1} tin nhắn</span>
          </div>
        </div>
      `;
    }).join('');

    sidebarSessionsList.querySelectorAll('.sidebar-session-item').forEach((item) => {
      item.addEventListener('click', () => {
        const sid = item.getAttribute('data-sid');
        if (sid) switchChatSession(sid);
      });
    });
  }

  window.deleteSidebarSession = async function(sid) {
    if (!sid) return;
    if (!confirm('Đồng chí có chắc chắn muốn xoá toàn bộ lịch sử của phiên trò chuyện này không? Thao tác này không thể hoàn tác.')) {
      return;
    }
    try {
      const res = await fetch(`/api/admin/sessions/${encodeURIComponent(sid)}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        showToast('✓ Đã xoá lịch sử phiên làm việc thành công', 'success');
        if (sid === sessionId) {
          messagesContainer.innerHTML = '';
          pendingAttachments = [];
          attachList.innerHTML = '';
          input.value = '';
          resizeInput();
          if (welcome) welcome.style.display = 'block';
          saveSessionId(generateUUID());
        }
        loadSidebarSessions();
      } else {
        showToast('Không thể xoá phiên làm việc', 'error');
      }
    } catch (err) {
      console.error('Lỗi khi xoá phiên:', err);
      showToast('Lỗi kết nối khi xoá phiên', 'error');
    }
  };


  async function switchChatSession(sid) {
    if (isSending) return;
    saveSessionId(sid);

    document.querySelectorAll('.sidebar-session-item').forEach((el) => {
      el.classList.toggle('active', el.getAttribute('data-sid') === sid);
    });

    closeMobileSidebar();

    messagesContainer.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:13px;">⏳ Đang tải nội dung phiên làm việc...</div>';
    if (welcome) welcome.style.display = 'none';

    try {
      const res = await fetch(`/api/admin/sessions/${encodeURIComponent(sid)}/messages`);
      if (!res.ok) throw new Error('Không thể tải tin nhắn phiên');
      const data = await res.json();
      const msgs = data.messages || [];

      messagesContainer.innerHTML = '';
      if (msgs.length === 0) {
        if (welcome) welcome.style.display = 'block';
        return;
      }

      msgs.forEach((m) => {
        if (m.message_text) {
          appendUserMessage(m.message_text, []);
        }
        if (m.bot_reply) {
          appendAssistantMessage({
            reply: m.bot_reply,
            model_used: m.model_used,
          });
        }
      });
      scrollToBottom();
    } catch (err) {
      showToast('Lỗi khi mở phiên: ' + err.message, 'error');
    }
  }

  // Tìm kiếm phiên trong Sidebar
  if (inputSearchSessionsSidebar) {
    inputSearchSessionsSidebar.addEventListener('input', () => {
      const kw = inputSearchSessionsSidebar.value.trim().toLowerCase();
      if (!kw) {
        renderSidebarSessions(allSidebarSessions);
        return;
      }
      const filtered = allSidebarSessions.filter((s) => {
        const t = (s.last_user_message || s.first_user_message || '').toLowerCase();
        return t.includes(kw);
      });
      renderSidebarSessions(filtered);
    });
  }

  // DOM Model Picker
  const btnModelPicker = document.getElementById('btnModelPicker');
  const modelPickerWrap = document.querySelector('.model-picker-wrap');
  const currentModelIcon = document.getElementById('currentModelIcon');
  const currentModelName = document.getElementById('currentModelName');
  const modelList = document.getElementById('modelList');
  const ollamaIndicator = document.getElementById('ollamaIndicator');

  // ============================================================================
  // 1. QUẢN LÝ MÔ HÌNH AI (OLLAMA LOCAL & CLOUD)
  // ============================================================================
  let availableModels = [];
  let currentActiveModel = '';

  async function loadModels() {
    try {
      const res = await fetch('/api/models');
      if (!res.ok) return;
      const data = await res.json();
      currentActiveModel = data.current_model;
      availableModels = data.models || [];

      if (ollamaIndicator) {
        if (data.ollama_online) {
          ollamaIndicator.className = 'local-badge';
          ollamaIndicator.textContent = 'Ollama Online';
        } else {
          ollamaIndicator.className = 'local-badge offline';
          ollamaIndicator.textContent = 'Ollama Offline';
        }
      }

      renderModelSelector();
    } catch (err) {
      console.warn('Lỗi khi tải danh sách mô hình:', err);
    }
  }

  function getModelIcon(m) {
    if (!m) return '⚡';
    if (m.provider === 'gemini') return '⚡';
    if (m.provider === 'local') {
      if (m.id && m.id.includes('3b')) return '🟢';
      if (m.id && m.id.includes('r1')) return '🟣';
      return '🔵';
    }
    return '☁️';
  }

  function renderModelSelector() {
    if (!modelList) return;
    modelList.innerHTML = '';

    const activeObj = availableModels.find(m => m.id === currentActiveModel);
    if (activeObj) {
      currentModelName.textContent = activeObj.name.split('—')[0].trim();
      currentModelIcon.textContent = getModelIcon(activeObj);
    }

    availableModels.forEach(m => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'model-item' + (m.id === currentActiveModel ? ' active' : '');
      const icon = getModelIcon(m);

      item.innerHTML = `
        <div class="model-item-top">
          <span class="model-item-title">${icon} ${m.name}</span>
          <span class="model-item-badge">${m.ram || (m.provider === 'local' ? 'Local' : (m.provider === 'gemini' ? 'Gemini Free' : 'Cloud'))}</span>
        </div>
        <div class="model-item-desc">${m.desc} ${m.provider === 'local' && !m.is_installed ? '<span style="color:var(--gold)">(Chưa tải)</span>' : ''}</div>
      `;

      item.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (modelPickerWrap) modelPickerWrap.classList.remove('open');
        await switchActiveModel(m.id, m.provider);
      });

      modelList.appendChild(item);
    });
  }

  async function switchActiveModel(modelId, provider) {
    try {
      if (currentModelName) currentModelName.textContent = 'Đang chuyển...';
      const res = await fetch('/api/models/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, provider: provider })
      });
      if (res.ok) {
        const data = await res.json();
        currentActiveModel = data.active_model;
        await checkStatus();
        await loadModels();
      }
    } catch (err) {
      console.error('Không thể chuyển mô hình:', err);
    }
  }

  // Toggle dropdown
  if (btnModelPicker && modelPickerWrap) {
    btnModelPicker.addEventListener('click', (e) => {
      e.stopPropagation();
      modelPickerWrap.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!modelPickerWrap.contains(e.target)) {
        modelPickerWrap.classList.remove('open');
      }
    });
  }

  // ============================================================================
  // 2. KIỂM TRA TRẠNG THÁI SERVER & AI
  // ============================================================================
  async function checkStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        let modelLabel = data.model_in_use || 'Gemini';
        if (data.is_local) {
          modelLabel = `Local AI (${data.model_in_use})`;
        } else if (data.is_gemini || data.provider === 'gemini') {
          modelLabel = `Google Gemini (${data.model_in_use}) [Chính]`;
        } else {
          modelLabel = `DeepSeek Cloud (${data.model_in_use || 'chat'}) [Dự phòng]`;
        }
        if (topbarModelName) {
          topbarModelName.textContent = data.is_gemini || data.provider === 'gemini' ? 'Gemini 3.5 Flash Lite' : modelLabel;
        }
        if (aiStatus) {
          aiStatus.className = data.ai_configured ? 'ai-status ok' : 'ai-status warn';
        }
        if (aiStatusText) {
          aiStatusText.textContent = data.ai_configured ? modelLabel : 'Chưa cấu hình API Key / Ollama';
        }
      }
    } catch {
      if (aiStatus) aiStatus.className = 'ai-status';
      if (aiStatusText) aiStatusText.textContent = 'Mất kết nối server';
    }
  }

  // ============================================================================
  // 2. SOẠN THẢO VÀ TỰ CO GIÃN TEXTAREA
  // ============================================================================
  function updateSendButton() {
    const hasText = input.value.trim().length > 0;
    const hasFiles = pendingAttachments.length > 0;
    btnSend.disabled = isSending || (!hasText && !hasFiles);
  }

  function resizeInput() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 220) + 'px';
    updateSendButton();
  }

  input.addEventListener('input', resizeInput);

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btnSend.disabled) {
        sendMessage();
      }
    }
  });

  // Gợi ý câu lệnh mẫu trên màn hình chào mừng
  document.querySelectorAll('.suggest').forEach((btn) => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        input.value = prompt;
        resizeInput();
        input.focus();
      }
    });
  });

  // ============================================================================
  // 3. ĐÍNH KÈM TỆP (BUTTON + KÉO THẢ)
  // ============================================================================
  btnAttach.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files || []);
    for (const f of files) {
      await uploadFile(f);
    }
    fileInput.value = '';
  });

  // Kéo thả tệp trên toàn cửa sổ (hỗ trợ cả Chat và Kho RAG thông minh)
  let dragCounter = 0;
  window.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragCounter++;
    const isRagActive = document.getElementById('subtab-rag')?.classList.contains('active') || document.getElementById('tab-rag')?.classList.contains('active');
    if (isRagActive) {
      const dropzone = document.getElementById('ragDropZone');
      if (dropzone) dropzone.classList.add('drag-active');
    } else {
      if (dropOverlay) dropOverlay.classList.add('show');
    }
  });

  window.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      if (dropOverlay) dropOverlay.classList.remove('show');
      const dropzone = document.getElementById('ragDropZone');
      if (dropzone) dropzone.classList.remove('drag-active');
    }
  });

  window.addEventListener('dragover', (e) => e.preventDefault());

  window.addEventListener('drop', async (e) => {
    e.preventDefault();
    dragCounter = 0;
    if (dropOverlay) dropOverlay.classList.remove('show');
    const dropzone = document.getElementById('ragDropZone');
    if (dropzone) dropzone.classList.remove('drag-active');

    const files = Array.from(e.dataTransfer?.files || []);
    if (files.length === 0) return;

    const isRagActive = document.getElementById('subtab-rag')?.classList.contains('active') || document.getElementById('tab-rag')?.classList.contains('active');
    if (isRagActive) {
      // Đang ở Tab Kho RAG -> Chuyển sang nạp và kiểm duyệt RAG
      if (window.processRagFileForPreview) {
        await window.processRagFileForPreview(files[0]);
      }
    } else {
      // Đang ở Tab Chat hoặc tab khác -> Đính kèm vào khung Chat
      for (const f of files) {
        await uploadFile(f);
      }
    }
  });

  async function uploadFile(file) {
    // Tạo chip trạng thái đang tải
    const tempId = 'temp_' + Math.random().toString(36).substring(2, 9);
    renderAttachChip({
      id: tempId,
      name: file.name,
      category_label: 'Đang tải lên...',
      isUploading: true,
    });

    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);

    try {
      const res = await fetch('/api/chat/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Lỗi khi tải tệp');
      }

      const data = await res.json();
      if (data.session_id) {
        saveSessionId(data.session_id);
      }

      // Xoá chip tạm và thêm chip chính thức
      removeChipElement(tempId);
      const att = data.attachment;
      pendingAttachments.push(att);
      renderAttachChip(att);
      updateSendButton();
    } catch (err) {
      removeChipElement(tempId);
      showToast(`Không thể đọc tệp ${file.name}: ${err.message}`, 'error');
    }
  }

  function renderAttachChip(att) {
    const chip = document.createElement('div');
    chip.className = 'chip' + (att.isUploading ? ' uploading' : '');
    chip.id = 'chip_' + att.id;
    chip.innerHTML = `
      <span>📎</span>
      <span class="cname" title="${escapeHtml(att.name)}">${escapeHtml(att.name)}</span>
      <span class="ctag">${escapeHtml(att.category_label || '')}</span>
      ${att.isUploading ? '' : `<button type="button" class="cx" title="Xoá tệp">✕</button>`}
    `;

    if (!att.isUploading) {
      chip.querySelector('.cx').addEventListener('click', async () => {
        await removeAttachment(att.id);
      });
    }

    attachList.appendChild(chip);
  }

  function removeChipElement(id) {
    const el = document.getElementById('chip_' + id);
    if (el) el.remove();
  }

  async function removeAttachment(attId) {
    try {
      await fetch('/api/chat/attachment/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, attachment_id: attId }),
      });
    } catch {}
    pendingAttachments = pendingAttachments.filter((a) => a.id !== attId);
    removeChipElement(attId);
    updateSendButton();
  }

  // ============================================================================
  // 4. GỬI TIN NHẮN VÀ HIỂN THỊ KẾT QUẢ
  // ============================================================================
  btnSend.addEventListener('click', () => sendMessage());

  async function sendMessage(overrideText = '', action = '') {
    if (isSending) return;

    const text = (overrideText || input.value).trim();
    const currentAtts = [...pendingAttachments];

    if (!text && !action && currentAtts.length === 0) return;

    if (text) {
      lastUserPrompt = text;
    }

    isSending = true;
    updateSendButton();

    // Ẩn màn hình chào mừng ở tin nhắn đầu tiên
    if (welcome) welcome.style.display = 'none';

    // Nếu không phải là bấm nút hành động ẩn thì thêm bóng tin nhắn của người dùng
    if (!action || text) {
      appendUserMessage(text || '(Gửi tệp đính kèm)', currentAtts);
    }

    // Xoá nội dung ô nhập và danh sách đính kèm đang chờ
    input.value = '';
    resizeInput();
    pendingAttachments = [];
    attachList.innerHTML = '';

    // Thêm bóng "đang suy nghĩ" của trợ lý
    const thinkingEl = appendThinkingMessage();
    scrollToBottom();

    try {
      const authToken = localStorage.getItem('cva_auth_token') || '';
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          action: action,
          token: authToken,
          attachment_ids: currentAtts.map((a) => a.id),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Lỗi kết nối máy chủ');
      }

      const data = await res.json();
      if (data.session_id) {
        saveSessionId(data.session_id);
      }

      thinkingEl.remove();
      appendAssistantMessage(data);

      // Cập nhật lại danh sách phiên ở Sidebar
      loadSidebarSessions();
    } catch (err) {
      thinkingEl.remove();
      appendAssistantMessage({
        reply: `❌ **Không thể hoàn thành yêu cầu:** ${err.message}\n\nĐồng chí vui lòng kiểm tra lại kết nối mạng hoặc khoá API trong tệp \`.env\`.`,
      });
    } finally {
      isSending = false;
      updateSendButton();
      scrollToBottom();
    }
  }

  // Cuộc trò chuyện mới
  btnNewChat.addEventListener('click', async () => {
    if (confirm('Bắt đầu cuộc trò chuyện mới? (Dự thảo chưa xuất Word sẽ bị xoá)')) {
      try {
        const authToken = localStorage.getItem('cva_auth_token') || '';
        const headers = { 'Content-Type': 'application/json' };
        if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

        const res = await fetch('/api/chat/reset', {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({ session_id: sessionId, token: authToken }),
        });
        const d = await res.json();
        saveSessionId(d.session_id);
      } catch {}

      messagesContainer.innerHTML = '';
      pendingAttachments = [];
      attachList.innerHTML = '';
      input.value = '';
      resizeInput();
      if (welcome) welcome.style.display = 'block';
      loadSidebarSessions();
    }
  });

  // ============================================================================
  // 5. RENDER CÁC THÀNH PHẦN TIN NHẮN
  // ============================================================================
  function appendUserMessage(text, atts) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-user';

    let filesHtml = '';
    if (atts && atts.length > 0) {
      filesHtml = `<div class="user-files">` +
        atts.map((a) => `<span class="chip"><span>📄</span><span class="cname">${escapeHtml(a.name)}</span></span>`).join('') +
        `</div>`;
    }

    wrap.innerHTML = `
      ${filesHtml}
      <div class="bubble">${escapeHtml(text)}</div>
    `;
    messagesContainer.appendChild(wrap);
  }

  function appendThinkingMessage() {
    const wrap = document.createElement('div');
    wrap.className = 'msg-ai';
    wrap.innerHTML = `
      <div class="avatar thinking"><img src="/static/assets/logo.png" alt="AI" class="avatar-img" /></div>
      <div class="content">
        <div class="thinking-text">
          <span>Chuyên viên ảo đang phân tích văn bản</span>
          <span class="dots"><span></span><span></span><span></span></span>
        </div>
      </div>
    `;
    messagesContainer.appendChild(wrap);
    return wrap;
  }

  function appendAssistantMessage(data) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-ai';

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = '<img src="/static/assets/logo.png" alt="AI" class="avatar-img" />';

    const content = document.createElement('div');
    content.className = 'content';

    // 1. Nội dung văn bản (markdown)
    const textHtml = parseMarkdown(data.reply || '');
    const textDiv = document.createElement('div');
    textDiv.innerHTML = textHtml;
    content.appendChild(textDiv);

    // 2. Khung xem trước văn bản hành chính (nếu có)
    if (data.preview && data.preview.length > 0) {
      data.preview.forEach((doc) => {
        content.appendChild(renderDocCard(doc));
      });
    }

    // 3. Tệp Word đã xuất sẵn để tải về
    if (data.files && data.files.length > 0) {
      const filesDiv = document.createElement('div');
      filesDiv.className = 'files';
      filesDiv.innerHTML = data.files.map((f) => `
        <a href="${escapeHtml(f.url)}" class="file-dl" target="_blank" download>
          <div class="ficon">W</div>
          <div class="fmeta">
            <div class="flabel">${escapeHtml(f.label || 'Tệp Word')}</div>
            <div class="fname">${escapeHtml(f.name)}</div>
          </div>
          <div class="fget">⬇ Tải về (.docx)</div>
        </a>
      `).join('');
      content.appendChild(filesDiv);
    }

    // 4. Các nút hành động (Duyệt, Huỷ, hoặc chọn Workflow)
    if (data.actions && data.actions.length > 0) {
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'actions';
      data.actions.forEach((act) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'act-btn' + (act.style === 'primary' ? ' primary' : '');
        btn.textContent = act.label;
        btn.addEventListener('click', () => {
          actionsDiv.querySelectorAll('.act-btn').forEach((b) => (b.disabled = true));
          sendMessage('', act.id);
        });
        actionsDiv.appendChild(btn);
      });
      content.appendChild(actionsDiv);
    }

    // 5. Thanh công cụ thao tác nhanh (Copy, Tái tạo, Model badge)
    const toolbarDiv = document.createElement('div');
    toolbarDiv.className = 'msg-actions-toolbar';

    const actionsLeft = document.createElement('div');
    actionsLeft.className = 'msg-actions-left';

    const btnCopy = document.createElement('button');
    btnCopy.type = 'button';
    btnCopy.className = 'btn-msg-action';
    btnCopy.innerHTML = '<span>📋</span> <span>Sao chép</span>';
    btnCopy.title = 'Sao chép toàn văn nội dung vào khay nhớ tạm';
    btnCopy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(data.reply || '');
        showToast('✓ Đã sao chép nội dung văn bản vào khay nhớ tạm!', 'success');
      } catch {
        showToast('Không thể tự động sao chép.', 'warning');
      }
    });
    actionsLeft.appendChild(btnCopy);

    if (lastUserPrompt) {
      const promptToRegen = lastUserPrompt;
      const btnRegen = document.createElement('button');
      btnRegen.type = 'button';
      btnRegen.className = 'btn-msg-action';
      btnRegen.innerHTML = '<span>🔄</span> <span>Tạo lại</span>';
      btnRegen.title = 'Yêu cầu Trợ lý AI tạo lại câu trả lời';
      btnRegen.addEventListener('click', () => {
        sendMessage(promptToRegen);
      });
      actionsLeft.appendChild(btnRegen);
    }
    toolbarDiv.appendChild(actionsLeft);

    const modelBadge = document.createElement('span');
    modelBadge.className = 'msg-meta-badge';
    modelBadge.textContent = data.model_used ? `🤖 ${data.model_used}` : '🤖 Chuyên viên ảo Công Hải Số';
    toolbarDiv.appendChild(modelBadge);

    content.appendChild(toolbarDiv);

    wrap.appendChild(avatar);
    wrap.appendChild(content);
    messagesContainer.appendChild(wrap);
  }

  // ============================================================================
  // 6. XEM TRƯỚC VĂN BẢN CHUẨN THỂ THỨC ĐẢNG (TRONG KHUNG CHAT)
  // ============================================================================
  function renderDocCard(doc) {
    const details = document.createElement('details');
    details.className = 'doc-card';
    details.open = true;

    const summary = document.createElement('summary');
    summary.innerHTML = `<span>📄</span> <strong>${escapeHtml(doc.label || 'Dự thảo văn bản')}</strong>`;

    const paper = document.createElement('div');
    paper.className = 'paper';

    const isCV = (doc.doc_type || '').toUpperCase() === 'CV';
    const cqTren = doc.co_quan_cap_tren || 'ĐẢNG BỘ TỈNH KHÁNH HOÀ';
    const cqBh = doc.co_quan_ban_hanh || 'ĐẢNG UỶ XÃ CÔNG HẢI';
    const soHieu = doc.so_hieu || 'Số      -CV/ĐU';
    const trichYeu = doc.trich_yeu || '';

    let html = `
      <div class="paper-hdr">
        <div class="l">
          <div>${escapeHtml(cqTren)}</div>
          <div><strong>${escapeHtml(cqBh)}</strong></div>
          <div>*</div>
          <div>${escapeHtml(soHieu)}</div>
          ${isCV ? `<div class="paper-cv-ty">${escapeHtml(trichYeu)}</div>` : ''}
        </div>
        <div class="r">
          <div><strong>ĐẢNG CỘNG SẢN VIỆT NAM</strong></div>
          <div class="line"></div>
          <div><i>Công Hải, ngày   tháng   năm 2026</i></div>
        </div>
      </div>
    `;

    if (!isCV) {
      html += `
        <div class="paper-title">
          <div class="tl">${escapeHtml((doc.ten_loai || '').toUpperCase())}</div>
          <div class="ty">${escapeHtml(trichYeu)}</div>
        </div>
      `;
    }

    if (doc.kinh_gui && doc.kinh_gui.length > 0) {
      const kgList = Array.isArray(doc.kinh_gui) ? doc.kinh_gui : [doc.kinh_gui];
      html += `
        <div class="paper-kg">
          <div class="k">Kính gửi:</div>
          <div>${kgList.map((x) => `<div>${escapeHtml(x)}</div>`).join('')}</div>
        </div>
      `;
    }

    if (doc.can_cu && Array.isArray(doc.can_cu)) {
      doc.can_cu.forEach((cc) => {
        html += `<p class="cc">${escapeHtml(cc)}</p>`;
      });
    }

    if (doc.noi_dung && Array.isArray(doc.noi_dung)) {
      doc.noi_dung.forEach((item) => {
        const text = typeof item === 'string' ? item : item.text || '';
        html += `<p>${formatPartyRun(text)}</p>`;
      });
    }

    const nnList = doc.noi_nhan || ['- Như trên;', '- Thường trực Đảng uỷ;', '- Lưu VPĐU.'];
    html += `
      <div class="paper-ftr">
        <div class="nn">
          <div class="nn-t">Nơi nhận:</div>
          ${nnList.map((n) => `<div>${escapeHtml(n)}</div>`).join('')}
        </div>
        <div class="sig">
          <div><strong>${escapeHtml(doc.tham_quyen || '')}</strong></div>
          <div>${escapeHtml(doc.chuc_vu || 'BÍ THƯ')}</div>
          <div class="gap"></div>
          <div><strong>${escapeHtml(doc.nguoi_ky || 'Vũ Thị Thuỳ Trang')}</strong></div>
        </div>
      </div>
    `;

    paper.innerHTML = html;
    details.appendChild(summary);
    details.appendChild(paper);
    return details;
  }

  function formatPartyRun(text) {
    let t = escapeHtml(text);
    // Bôi đậm markdown **text**
    t = t.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return t;
  }

  // ============================================================================
  // 7. PARSER MARKDOWN NHẸ (CHO BẢNG, DANH SÁCH, ĐOẠN VĂN)
  // ============================================================================
  function parseMarkdown(md) {
    if (!md) return '';

    // Tách dòng
    const lines = md.split('\n');
    let out = [];
    let inTable = false;
    let tableRows = [];
    let inList = false;

    function flushTable() {
      if (!inTable) return;
      let html = '<div class="table-wrap"><table>';
      tableRows.forEach((row, i) => {
        if (i === 1 && row.every((c) => /^-+$/.test(c.trim()))) return; // separator
        const tag = i === 0 ? 'th' : 'td';
        html += '<tr>' + row.map((c) => `<${tag}>${formatInline(c.trim())}</${tag}>`).join('') + '</tr>';
      });
      html += '</table></div>';
      out.push(html);
      inTable = false;
      tableRows = [];
    }

    function flushList() {
      if (inList) {
        out.push('</ul>');
        inList = false;
      }
    }

    lines.forEach((line) => {
      const trimmed = line.trim();

      // Bảng biểu | a | b |
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        flushList();
        inTable = true;
        const cols = trimmed.slice(1, -1).split('|');
        tableRows.push(cols);
        return;
      } else {
        flushTable();
      }

      // Blockquote trích dẫn >
      if (trimmed.startsWith('> ')) {
        flushList();
        out.push(`<blockquote>${formatInline(trimmed.slice(2))}</blockquote>`);
        return;
      }

      // Tiêu đề ###
      if (trimmed.startsWith('### ')) {
        flushList();
        out.push(`<h3>${formatInline(trimmed.slice(4))}</h3>`);
        return;
      }
      if (trimmed.startsWith('## ')) {
        flushList();
        out.push(`<h3>${formatInline(trimmed.slice(3))}</h3>`);
        return;
      }

      // Danh sách gạch đầu dòng
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        if (!inList) {
          out.push('<ul>');
          inList = true;
        }
        out.push(`<li>${formatInline(trimmed.slice(2))}</li>`);
        return;
      }

      // Danh sách đánh số 1.
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
      if (numMatch) {
        flushList();
        out.push(`<p><strong>${numMatch[1]}.</strong> ${formatInline(numMatch[2])}</p>`);
        return;
      }

      flushList();

      if (!trimmed) {
        // Dòng trống
        return;
      }

      out.push(`<p>${formatInline(trimmed)}</p>`);
    });

    flushTable();
    flushList();
    return out.join('');
  }

  function formatInline(str) {
    let s = escapeHtml(str);
    s = s.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    return s;
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function scrollToBottom() {
    setTimeout(() => {
      chatScroll.scrollTop = chatScroll.scrollHeight;
    }, 50);
  }

  // ============================================================================
  // 7. ĐIỀU HƯỚNG VIEW (CHAT vs ADMIN) & SUBTABS ADMIN
  // ============================================================================
  const viewChat = document.getElementById('view-chat');
  const viewAdmin = document.getElementById('view-admin');
  const adminSwitchBar = document.getElementById('adminSwitchBar');
  const btnSwitchChat = document.getElementById('btnSwitchChat');
  const btnSwitchAdmin = document.getElementById('btnSwitchAdmin');
  const btnBackToChatFromAdmin = document.getElementById('btnBackToChatFromAdmin');
  const welcomeUserName = document.getElementById('welcomeUserName');

  function showView(viewName) {
    if (viewName === 'admin') {
      if (!currentCadre || currentCadre.vai_tro !== 'admin') {
        showToast('⚠️ Chỉ Quản trị viên (Admin) mới có quyền truy cập vào Bảng điều hành!', 'warning');
        return;
      }
      if (viewChat) { viewChat.style.display = 'none'; viewChat.classList.remove('active'); }
      if (viewAdmin) { viewAdmin.style.display = 'flex'; viewAdmin.classList.add('active'); }
      if (btnSwitchAdmin) btnSwitchAdmin.classList.add('active');
      if (btnSwitchChat) btnSwitchChat.classList.remove('active');
      if (chatSidebar) chatSidebar.classList.add('collapsed');
      closeMobileSidebar();

      // Đảm bảo hiển thị đúng phân hệ đang được chọn
      const currentActiveTab = document.querySelector('.admin-subtab.active') || adminSubtabs[0];
      const targetSubtabId = currentActiveTab ? currentActiveTab.getAttribute('data-subtab') : 'subtab-cadres';
      adminSubcontents.forEach(c => {
        if (c.id === targetSubtabId) {
          c.classList.add('active');
          c.style.display = 'block';
        } else {
          c.classList.remove('active');
          c.style.display = 'none';
        }
      });

      loadAdminDashboard();
    } else {
      if (viewAdmin) { viewAdmin.style.display = 'none'; viewAdmin.classList.remove('active'); }
      if (viewChat) { viewChat.style.display = 'flex'; viewChat.classList.add('active'); }
      if (btnSwitchChat) btnSwitchChat.classList.add('active');
      if (btnSwitchAdmin) btnSwitchAdmin.classList.remove('active');
    }
  }

  if (btnSwitchChat) btnSwitchChat.addEventListener('click', () => showView('chat'));
  if (btnSwitchAdmin) btnSwitchAdmin.addEventListener('click', () => showView('admin'));
  if (btnBackToChatFromAdmin) btnBackToChatFromAdmin.addEventListener('click', () => showView('chat'));

  // Admin Subtabs switching
  const adminSubtabs = document.querySelectorAll('.admin-subtab');
  const adminSubcontents = document.querySelectorAll('.admin-subcontent');

  adminSubtabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-subtab');
      adminSubtabs.forEach(t => t.classList.remove('active'));
      adminSubcontents.forEach(c => {
        c.classList.remove('active');
        c.style.display = 'none';
      });

      tab.classList.add('active');
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add('active');
        targetContent.style.display = 'block';
      }

      if (targetId === 'subtab-cadres') loadAdminCadres();
      if (targetId === 'subtab-models') checkStatus();
      if (targetId === 'subtab-logs') loadAdminChatLogs();
      if (targetId === 'subtab-tasks') loadTasks();
      if (targetId === 'subtab-rag') {
        loadRagStats();
        loadRagDocuments();
      }
      if (targetId === 'subtab-server') loadAdminServerLogs();
    });
  });

  // --- SỔ NHIỆM VỤ (TABLE & KANBAN) ---
  const tasksTableBody = document.getElementById('tasksTableBody');
  const filterTaskUnit = document.getElementById('filterTaskUnit');
  const filterTaskStatus = document.getElementById('filterTaskStatus');
  const btnRefreshTasks = document.getElementById('btnRefreshTasks');
  const btnTaskViewTable = document.getElementById('btnTaskViewTable');
  const btnTaskViewKanban = document.getElementById('btnTaskViewKanban');
  const tasksTableView = document.getElementById('tasksTableView');
  const tasksKanbanView = document.getElementById('tasksKanbanView');

  // Stats elements
  const statTasksTotal = document.getElementById('statTasksTotal');
  const statTasksPending = document.getElementById('statTasksPending');
  const statTasksInprogress = document.getElementById('statTasksInprogress');
  const statTasksCompleted = document.getElementById('statTasksCompleted');
  const statTasksRescheduled = document.getElementById('statTasksRescheduled');
  const inputSearchTasks = document.getElementById('inputSearchTasks');
  const btnClearTaskSearch = document.getElementById('btnClearTaskSearch');
  const taskStatusTabs = document.getElementById('taskStatusTabs');

  // Kanban column wraps
  const kanbanPendingWrap = document.getElementById('kanbanPendingWrap');
  const kanbanInprogressWrap = document.getElementById('kanbanInprogressWrap');
  const kanbanCompletedWrap = document.getElementById('kanbanCompletedWrap');
  const kanbanRescheduledWrap = document.getElementById('kanbanRescheduledWrap');
  const countKanbanPending = document.getElementById('countKanbanPending');
  const countKanbanInprogress = document.getElementById('countKanbanInprogress');
  const countKanbanCompleted = document.getElementById('countKanbanCompleted');
  const countKanbanRescheduled = document.getElementById('countKanbanRescheduled');

  let currentTasksData = [];
  let activeTaskStatusFilter = '';
  let activeTaskSearchKeyword = '';

  if (btnTaskViewTable && btnTaskViewKanban) {
    btnTaskViewTable.addEventListener('click', () => {
      btnTaskViewTable.classList.add('active');
      btnTaskViewKanban.classList.remove('active');
      if (tasksTableView) tasksTableView.style.display = 'block';
      if (tasksKanbanView) tasksKanbanView.style.display = 'none';
    });
    btnTaskViewKanban.addEventListener('click', () => {
      btnTaskViewKanban.classList.add('active');
      btnTaskViewTable.classList.remove('active');
      if (tasksTableView) tasksTableView.style.display = 'none';
      if (tasksKanbanView) tasksKanbanView.style.display = 'block';
    });
  }

  // Filter Tabs Event Listeners (Linear Style)
  if (taskStatusTabs) {
    taskStatusTabs.addEventListener('click', (e) => {
      const btn = e.target.closest('.task-tab-btn');
      if (!btn) return;
      taskStatusTabs.querySelectorAll('.task-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTaskStatusFilter = btn.getAttribute('data-status') || '';
      renderFilteredTasks();
    });
  }

  // Live Instant Search Event Listeners
  if (inputSearchTasks) {
    inputSearchTasks.addEventListener('input', () => {
      activeTaskSearchKeyword = inputSearchTasks.value.toLowerCase().trim();
      if (btnClearTaskSearch) {
        btnClearTaskSearch.style.display = activeTaskSearchKeyword ? 'inline-flex' : 'none';
      }
      renderFilteredTasks();
    });
  }

  if (btnClearTaskSearch) {
    btnClearTaskSearch.addEventListener('click', () => {
      if (inputSearchTasks) inputSearchTasks.value = '';
      activeTaskSearchKeyword = '';
      btnClearTaskSearch.style.display = 'none';
      renderFilteredTasks();
    });
  }

  if (filterTaskUnit) filterTaskUnit.addEventListener('change', renderFilteredTasks);
  if (filterTaskStatus) filterTaskStatus.addEventListener('change', () => {
    activeTaskStatusFilter = filterTaskStatus.value;
    if (taskStatusTabs) {
      taskStatusTabs.querySelectorAll('.task-tab-btn').forEach(b => {
        b.classList.toggle('active', (b.getAttribute('data-status') || '') === activeTaskStatusFilter);
      });
    }
    renderFilteredTasks();
  });
  if (btnRefreshTasks) btnRefreshTasks.addEventListener('click', loadTasks);

  async function loadTasks() {
    if (!tasksTableBody) return;
    tasksTableBody.innerHTML = '<tr><td colspan="5" class="loading-td">Đang tải Sổ nhiệm vụ...</td></tr>';
    try {
      const res = await fetch('/api/tasks');
      const data = await res.json();
      currentTasksData = data.tasks || [];

      // Cập nhật số đếm thống kê tổng và theo cột
      const pendingAll = currentTasksData.filter(t => t.trang_thai === 'Chưa thực hiện');
      const inprogressAll = currentTasksData.filter(t => t.trang_thai === 'Đang thực hiện');
      const completedAll = currentTasksData.filter(t => t.trang_thai === 'Hoàn thành');
      const rescheduledAll = currentTasksData.filter(t => t.trang_thai === 'Chuyển tiếp tháng sau');

      if (statTasksTotal) statTasksTotal.textContent = currentTasksData.length;
      if (statTasksPending) statTasksPending.textContent = pendingAll.length;
      if (statTasksInprogress) statTasksInprogress.textContent = inprogressAll.length;
      if (statTasksCompleted) statTasksCompleted.textContent = completedAll.length;
      if (statTasksRescheduled) statTasksRescheduled.textContent = rescheduledAll.length;

      if (countKanbanPending) countKanbanPending.textContent = pendingAll.length;
      if (countKanbanInprogress) countKanbanInprogress.textContent = inprogressAll.length;
      if (countKanbanCompleted) countKanbanCompleted.textContent = completedAll.length;
      if (countKanbanRescheduled) countKanbanRescheduled.textContent = rescheduledAll.length;

      renderFilteredTasks();
    } catch (err) {
      tasksTableBody.innerHTML = `<tr><td colspan="5" style="color:#ef4444; padding:20px;">Lỗi tải dữ liệu: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function renderFilteredTasks() {
    if (!tasksTableBody) return;
    const selectedUnit = filterTaskUnit ? filterTaskUnit.value : '';

    const filtered = currentTasksData.filter(t => {
      if (activeTaskStatusFilter && t.trang_thai !== activeTaskStatusFilter) return false;
      if (selectedUnit && t.co_quan_chu_tri !== selectedUnit) return false;
      if (activeTaskSearchKeyword) {
        const text = `${t.task_id} ${t.noi_dung_nhiem_vu || ''} ${t.so_hieu_vb || ''} ${t.co_quan_chu_tri || ''} ${t.cap_trinh || ''}`.toLowerCase();
        if (!text.includes(activeTaskSearchKeyword)) return false;
      }
      return true;
    });

    // 1. Render Table View (Linear / Notion Style 4-5 Cột Cốt Lõi)
    if (filtered.length === 0) {
      tasksTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 32px; color:var(--text-muted); font-size:13px;">Không có nhiệm vụ nào phù hợp với bộ lọc.</td></tr>';
    } else {
      tasksTableBody.innerHTML = filtered.map(t => {
        let slug = 'pending';
        if (t.trang_thai === 'Đang thực hiện') slug = 'inprogress';
        if (t.trang_thai === 'Hoàn thành') slug = 'completed';
        if (t.trang_thai === 'Chuyển tiếp tháng sau') slug = 'rescheduled';

        const isDone = t.trang_thai === 'Hoàn thành';
        const isUrgent = t.muc_do_uu_tien === 'Khẩn';

        return `
          <tr class="${isDone ? 'task-row-done' : ''}">
            <td style="text-align: center; vertical-align: middle;">
              <button type="button" class="btn-task-circle ${isDone ? 'checked' : ''}" onclick="window.markTaskDone('${t.task_id}', ${isDone ? "'Chưa thực hiện'" : "'Hoàn thành'"})" title="${isDone ? 'Bấm để chuyển về Chưa hoàn thành' : 'Bấm để đánh dấu Hoàn thành'}">
                ${isDone ? '✓' : ''}
              </button>
            </td>
            <td>
              <div class="task-cell-main">
                <div class="task-title ${isDone ? 'task-done-title' : ''}">${escapeHtml(t.noi_dung_nhiem_vu)}</div>
                <div class="task-meta-line">
                  <span class="meta-vb">📄 ${escapeHtml(t.so_hieu_vb || 'Văn bản Đảng')}</span>
                  ${t.cap_trinh ? `<span class="meta-sep">•</span><span class="meta-cap">Cấp trình: ${escapeHtml(t.cap_trinh)}</span>` : ''}
                  <span class="meta-sep">•</span><span class="meta-id">${escapeHtml(t.task_id)}</span>
                </div>
              </div>
            </td>
            <td style="vertical-align: middle;">
              <span class="task-unit-tag">${escapeHtml(t.co_quan_chu_tri || 'UBND xã')}</span>
            </td>
            <td style="vertical-align: middle;">
              <div class="task-deadline-cell">
                <span>📅 ${escapeHtml(t.deadline_date || '-')}</span>
                ${isUrgent ? '<span class="priority-urgent-pill">Khẩn</span>' : ''}
              </div>
            </td>
            <td style="text-align: right; vertical-align: middle;">
              <span class="status-pill status-${slug}"><span class="status-dot"></span>${escapeHtml(t.trang_thai)}</span>
            </td>
          </tr>
        `;
      }).join('');
    }

    // 2. Render Kanban Columns (Minimal Clean Board)
    function renderKanbanCard(t) {
      const isDone = t.trang_thai === 'Hoàn thành';
      const isUrgent = t.muc_do_uu_tien === 'Khẩn';
      return `
        <div class="kanban-card ${isDone ? 'kanban-card-done' : ''}">
          <div class="kanban-card-top">
            <span class="kanban-card-id">${escapeHtml(t.task_id)}</span>
            <span class="task-unit-tag">${escapeHtml(t.co_quan_chu_tri || 'UBND xã')}</span>
          </div>
          <div class="kanban-card-title ${isDone ? 'task-done-title' : ''}">${escapeHtml(t.noi_dung_nhiem_vu)}</div>
          ${t.so_hieu_vb ? `<div class="kanban-card-vb">📄 ${escapeHtml(t.so_hieu_vb)}</div>` : ''}
          <div class="kanban-card-footer">
            <span class="kanban-deadline">📅 ${escapeHtml(t.deadline_date || 'Không hạn')}</span>
            ${isUrgent ? '<span class="priority-urgent-pill">Khẩn</span>' : ''}
            <button type="button" class="btn-kanban-toggle ${isDone ? 'done' : ''}" onclick="window.markTaskDone('${t.task_id}', ${isDone ? "'Chưa thực hiện'" : "'Hoàn thành'"})" title="${isDone ? 'Đánh dấu chưa xong' : 'Đánh dấu hoàn thành'}">
              ${isDone ? '✓ Đã xong' : '○ Hoàn thành'}
            </button>
          </div>
        </div>
      `;
    }

    const emptyColHtml = '<div class="kanban-empty-col">Không có nhiệm vụ</div>';
    const pendingFiltered = filtered.filter(t => t.trang_thai === 'Chưa thực hiện');
    const inprogressFiltered = filtered.filter(t => t.trang_thai === 'Đang thực hiện');
    const completedFiltered = filtered.filter(t => t.trang_thai === 'Hoàn thành');
    const rescheduledFiltered = filtered.filter(t => t.trang_thai === 'Chuyển tiếp tháng sau');

    if (kanbanPendingWrap) kanbanPendingWrap.innerHTML = pendingFiltered.length ? pendingFiltered.map(renderKanbanCard).join('') : emptyColHtml;
    if (kanbanInprogressWrap) kanbanInprogressWrap.innerHTML = inprogressFiltered.length ? inprogressFiltered.map(renderKanbanCard).join('') : emptyColHtml;
    if (kanbanCompletedWrap) kanbanCompletedWrap.innerHTML = completedFiltered.length ? completedFiltered.map(renderKanbanCard).join('') : emptyColHtml;
    if (kanbanRescheduledWrap) kanbanRescheduledWrap.innerHTML = rescheduledFiltered.length ? rescheduledFiltered.map(renderKanbanCard).join('') : emptyColHtml;
  }

  window.markTaskDone = async function(taskId, nextStatus = 'Hoàn thành') {
    try {
      const res = await fetch(`/api/tasks/${taskId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trang_thai: nextStatus, ket_qua_bao_cao: nextStatus === 'Hoàn thành' ? 'Đã hoàn thành báo cáo' : '' })
      });
      if (res.ok) {
        showToast(nextStatus === 'Hoàn thành' ? '✓ Đã hoàn thành nhiệm vụ!' : '↺ Đã chuyển lại Chưa thực hiện!', 'success');
        await loadTasks();
      }
    } catch (err) {
      showToast('Lỗi cập nhật nhiệm vụ: ' + err.message, 'error');
    }
  };

  // ============================================================================
  // --- KHO VĂN BẢN RAG CÓ KIỂM SOÁT (HUMAN-IN-THE-LOOP INGESTION) ---
  // ============================================================================
  const btnUploadForRag = document.getElementById('btnUploadForRag');
  const btnClearRag = document.getElementById('btnClearRag');
  const ragFileInput = document.getElementById('ragFileInput');
  const btnRefreshRagDocs = document.getElementById('btnRefreshRagDocs');

  const statRagDocs = document.getElementById('statRagDocs');
  const statRagChunks = document.getElementById('statRagChunks');
  const statRagCore = document.getElementById('statRagCore');
  const statRagThematic = document.getElementById('statRagThematic');

  const ragDocsTableBody = document.getElementById('ragDocsTableBody');
  const ragSearchInput = document.getElementById('ragSearchInput');
  const btnRagSearch = document.getElementById('btnRagSearch');
  const ragResultsWrap = document.getElementById('ragResultsWrap');

  // Modal Review Elements
  const modalRagReview = document.getElementById('modalRagReview');
  const btnCloseRagModal = document.getElementById('btnCloseRagModal');
  const btnCancelRagReview = document.getElementById('btnCancelRagReview');
  const btnCommitRag = document.getElementById('btnCommitRag');

  const reviewFileNotice = document.getElementById('reviewFileNotice');
  const reviewSoHieu = document.getElementById('reviewSoHieu');
  const reviewNgay = document.getElementById('reviewNgay');
  const reviewCoQuan = document.getElementById('reviewCoQuan');
  const reviewCoQuanCode = document.getElementById('reviewCoQuanCode');
  const reviewTheLoai = document.getElementById('reviewTheLoai');
  const reviewVongDoi = document.getElementById('reviewVongDoi');
  const reviewChuyenDe = document.getElementById('reviewChuyenDe');
  const wrapNewChuyenDe = document.getElementById('wrapNewChuyenDe');
  const inputNewChuyenDe = document.getElementById('inputNewChuyenDe');
  const btnSaveNewChuyenDe = document.getElementById('btnSaveNewChuyenDe');
  const reviewTrichYeu = document.getElementById('reviewTrichYeu');
  const reviewThayThe = document.getElementById('reviewThayThe');
  const reviewChunksPreview = document.getElementById('reviewChunksPreview');

  let currentRagPreviewData = null;

  // 1. Tải số liệu thống kê kho RAG
  async function loadRagStats() {
    try {
      const res = await fetch('/api/rag/stats');
      if (!res.ok) return;
      const d = await res.json();
      if (statRagDocs) statRagDocs.textContent = d.total_docs || d.total_documents || 0;
      if (statRagChunks) statRagChunks.textContent = d.total_chunks || 0;
      if (statRagCore) statRagCore.textContent = d.core_docs || d.core_directives || 0;
      if (statRagThematic) statRagThematic.textContent = d.thematic_docs || d.thematic_cases || 0;
    } catch (err) {
      console.warn('Lỗi tải thống kê RAG:', err);
    }
  }

  // Tải danh mục chuyên đề công tác vào Dropdown
  async function loadThematics(selectedCode = '') {
    if (!reviewChuyenDe) return;
    try {
      const res = await fetch('/api/rag/thematics');
      if (!res.ok) return;
      const data = await res.json();
      const list = data.thematics || [];

      let html = list.map(c => `<option value="${escapeHtml(c.ma_chuyen_de)}">${escapeHtml(c.ten_chuyen_de)}</option>`).join('');
      html += '<option value="__NEW__">➕ Thêm chuyên đề mới...</option>';
      reviewChuyenDe.innerHTML = html;

      if (selectedCode) {
        reviewChuyenDe.value = selectedCode;
      }
    } catch (err) {
      console.warn('Lỗi tải danh mục chuyên đề:', err);
    }
  }

  // Sự kiện chọn hoặc thêm chuyên đề mới
  if (reviewChuyenDe) {
    reviewChuyenDe.addEventListener('change', () => {
      if (reviewChuyenDe.value === '__NEW__') {
        if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'block';
        if (inputNewChuyenDe) inputNewChuyenDe.focus();
      } else {
        if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'none';
      }
    });
  }

  if (btnSaveNewChuyenDe && inputNewChuyenDe) {
    btnSaveNewChuyenDe.addEventListener('click', async () => {
      const name = inputNewChuyenDe.value.trim();
      if (!name) {
        showToast('Vui lòng nhập tên chuyên đề mới!', 'warning');
        inputNewChuyenDe.focus();
        return;
      }
      try {
        btnSaveNewChuyenDe.disabled = true;
        btnSaveNewChuyenDe.textContent = '⏳ Đang lưu...';
        const res = await fetch('/api/rag/thematics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ten_chuyen_de: name })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`✓ Đã thêm chuyên đề mới "${name}" thành công!`, 'success');
          inputNewChuyenDe.value = '';
          if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'none';
          await loadThematics(data.thematic.ma_chuyen_de);
        } else {
          showToast('Lỗi: ' + (data.detail || 'Không thể tạo chuyên đề'), 'error');
        }
      } catch (err) {
        showToast('Lỗi kết nối: ' + err.message, 'error');
      } finally {
        btnSaveNewChuyenDe.disabled = false;
        btnSaveNewChuyenDe.textContent = '+ Thêm ngay';
      }
    });
  }

  // 2. State & Điều khiển Kho RAG Đa Chiều (Phân Trang & Bộ Lọc Linear)
  let allRagDocs = [];
  let filteredRagDocs = [];
  let currentRagPage = 1;
  let ragPageSize = 20;
  let currentRagLifecycleFilter = '';
  let ragSortField = 'ngay_ban_hanh';
  let ragSortOrder = 'desc';
  let ragSearchDebounceTimer = null;

  // DOM Elements Kho RAG
  const ragLifecycleTabs = document.getElementById('ragLifecycleTabs');
  const ragQuickSearch = document.getElementById('ragQuickSearch');
  const btnClearQuickSearch = document.getElementById('btnClearQuickSearch');
  const ragFilterType = document.getElementById('ragFilterType');
  const ragFilterYear = document.getElementById('ragFilterYear');
  const ragFilterLifecycle = document.getElementById('ragFilterLifecycle');
  const ragFilterIssuer = document.getElementById('ragFilterIssuer');
  const btnResetRagFilters = document.getElementById('btnResetRagFilters');
  const ragViewSwitcher = document.getElementById('ragViewSwitcher');
  const ragPageSizeSelect = document.getElementById('ragPageSizeSelect');
  const ragSortSelect = document.getElementById('ragSortSelect');
  const btnExpandAllCats = document.getElementById('btnExpandAllCats');
  const btnCollapseAllCats = document.getElementById('btnCollapseAllCats');
  const btnExpandAllYears = document.getElementById('btnExpandAllYears');
  const btnCollapseAllYears = document.getElementById('btnCollapseAllYears');
  const ragTableView = document.getElementById('ragTableView');
  const ragCategoryView = document.getElementById('ragCategoryView');
  const ragYearView = document.getElementById('ragYearView');
  const ragCountVisible = document.getElementById('ragCountVisible');
  const ragCountTotal = document.getElementById('ragCountTotal');
  const ragFilterNotice = document.getElementById('ragFilterNotice');
  const ragCategoryGroupsWrap = document.getElementById('ragCategoryGroupsWrap');
  const ragYearGroupsWrap = document.getElementById('ragYearGroupsWrap');

  const btnToggleFtsWrap = document.getElementById('btnToggleFtsWrap');
  const ragFtsPanel = document.getElementById('ragFtsPanel');
  const btnCloseFtsPanel = document.getElementById('btnCloseFtsPanel');

  const ragPaginationBar = document.getElementById('ragPaginationBar');
  const ragPaginationInfo = document.getElementById('ragPaginationInfo');
  const ragPaginationControls = document.getElementById('ragPaginationControls');

  // Gắn sự kiện chuyển Linear Filter Tabs cho Kho RAG
  if (ragLifecycleTabs) {
    const tabBtns = ragLifecycleTabs.querySelectorAll('.task-tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentRagLifecycleFilter = btn.getAttribute('data-lifecycle') || '';
        currentRagPage = 1;
        applyRagFiltersAndRender();
      });
    });
  }

  // Helper ánh xạ tên thể loại văn bản Đảng chuẩn
  const THE_LOAI_MAP = {
    'KH': 'Kế hoạch (-KH/ĐU)',
    'NQ': 'Nghị quyết (-NQ/ĐU)',
    'CV': 'Công văn (-CV/ĐU)',
    'BC': 'Báo cáo (-BC/ĐU)',
    'QĐ': 'Quyết định (-QĐ/ĐU)',
    'KL': 'Kết luận (-KL/ĐU)',
    'TB': 'Thông báo (-TB/ĐU)',
    'TTr': 'Tờ trình (-TTr/ĐU)',
    'CT': 'Chỉ thị (-CT/ĐU)',
    'CTr': 'Chương trình (-CTr/ĐU)',
    'HD': 'Hướng dẫn (-HD/ĐU)',
    'QC': 'Quy chế (-QC/ĐU)',
    'QD': 'Quy định (-QyĐ/ĐU)',
    'PA': 'Phương án (-PA/ĐU)',
    'DA': 'Đề án (-ĐA/ĐU)'
  };

  function getTheLoaiFullName(code) {
    if (!code) return 'Khác';
    const c = String(code).trim().toUpperCase();
    return THE_LOAI_MAP[c] || `Văn bản thể loại ${c}`;
  }

  // Helper sinh dòng HTML cho 1 văn bản (5 cột tinh gọn, rõ ràng)
  function buildDocTableRowHtml(doc) {
    let badgeVongDoi = '<span class="task-badge badge-review">🎯 Chuyên đề</span>';
    if (doc.nhom_vong_doi === 'CORE_DIRECTIVE') {
      badgeVongDoi = '<span class="task-badge badge-assigned">🏛️ Nền tảng</span>';
    } else if (doc.nhom_vong_doi === 'EPHEMERAL_EVENT') {
      badgeVongDoi = '<span class="task-badge badge-draft">⚡ Sự vụ</span>';
    }

    const soHieu = escapeHtml(doc.so_hieu_vb || 'Chưa có số');
    const theLoai = escapeHtml(doc.the_loai_vb || doc.the_loai || 'VB');
    const ngayBH = escapeHtml(doc.ngay_ban_hanh || '');
    const coQuan = escapeHtml(doc.co_quan_ban_hanh || 'Cấp uỷ');
    const signer = doc.nguoi_ky ? `<div class="rag-doc-signer">✍️ ${escapeHtml(doc.nguoi_ky)}</div>` : '';
    const chuyenDe = doc.ten_chuyen_de ? `<div class="rag-doc-sub-thematic">📂 ${escapeHtml(doc.ten_chuyen_de)}</div>` : '';
    const chunkCount = doc.chunk_count || 1;

    return `
      <tr class="rag-table-row">
        <td>
          <div class="rag-doc-sohieu">${soHieu}</div>
          <div class="rag-doc-meta-sub">
            <span class="badge-theloai">${theLoai}</span>
            ${ngayBH ? `<span class="rag-doc-date">📅 ${ngayBH}</span>` : ''}
          </div>
        </td>
        <td>
          <div class="rag-doc-issuer">${coQuan}</div>
          ${signer}
          ${chuyenDe}
        </td>
        <td>
          <div class="rag-doc-summary" title="${escapeHtml(doc.trich_yeu || '')}">${escapeHtml(doc.trich_yeu || 'Không có trích yếu')}</div>
        </td>
        <td style="text-align: center;">
          <div style="margin-bottom: 4px;">${badgeVongDoi}</div>
          <span class="task-unit-tag">${chunkCount} chunk${chunkCount > 1 ? 's' : ''}</span>
        </td>
        <td style="text-align: center; white-space: nowrap;">
          <button class="btn-chs-outline" style="padding: 4px 10px; font-size: 12px;" onclick="window.openRagDocDetail('${escapeHtml(doc.doc_id)}')" title="Xem chi tiết các đoạn trích và chỉnh sửa">👁️ Chi tiết</button>
          <button class="btn-chs-outline" style="padding: 4px 8px; font-size: 12px; color: #ef4444; border-color: rgba(239,68,68,0.25);" onclick="window.deleteRagDocument('${escapeHtml(doc.doc_id)}', '${escapeHtml(doc.so_hieu_vb || '')}')" title="Xoá văn bản">🗑️</button>
        </td>
      </tr>
    `;
  }

  // Tự động trích xuất các tuỳ chọn lọc từ dữ liệu thực tế
  function populateFilterDropdowns(docs) {
    if (!docs || docs.length === 0) return;

    // 1. Thể loại
    if (ragFilterType) {
      const currentVal = ragFilterType.value;
      const typeCounts = {};
      docs.forEach(d => {
        const t = (d.the_loai_vb || d.the_loai || 'KHAC').trim().toUpperCase();
        typeCounts[t] = (typeCounts[t] || 0) + 1;
      });
      const sortedTypes = Object.keys(typeCounts).sort((a, b) => typeCounts[b] - typeCounts[a]);
      let typeHtml = `<option value="">Tất cả Thể loại (${docs.length})</option>`;
      sortedTypes.forEach(t => {
        const label = THE_LOAI_MAP[t] || t;
        typeHtml += `<option value="${escapeHtml(t)}">${escapeHtml(label)} (${typeCounts[t]})</option>`;
      });
      ragFilterType.innerHTML = typeHtml;
      if (currentVal && typeCounts[currentVal]) ragFilterType.value = currentVal;
    }

    // 2. Năm ban hành
    if (ragFilterYear) {
      const currentVal = ragFilterYear.value;
      const yearCounts = {};
      docs.forEach(d => {
        let y = d.nam_ban_hanh;
        if (!y && d.ngay_ban_hanh) {
          const parts = String(d.ngay_ban_hanh).split(/[-\/]/);
          if (parts.length >= 3) y = parts[0].length === 4 ? parts[0] : parts[2];
        }
        if (y) yearCounts[y] = (yearCounts[y] || 0) + 1;
      });
      const sortedYears = Object.keys(yearCounts).sort((a, b) => b - a);
      let yearHtml = `<option value="">Tất cả Năm (${docs.length})</option>`;
      sortedYears.forEach(y => {
        yearHtml += `<option value="${escapeHtml(y)}">Năm ${escapeHtml(y)} (${yearCounts[y]})</option>`;
      });
      ragFilterYear.innerHTML = yearHtml;
      if (currentVal && yearCounts[currentVal]) ragFilterYear.value = currentVal;
    }

    // 3. Cơ quan ban hành
    if (ragFilterIssuer) {
      const currentVal = ragFilterIssuer.value;
      const issuerCounts = {};
      docs.forEach(d => {
        const issuer = (d.co_quan_ban_hanh || 'Khác').trim();
        issuerCounts[issuer] = (issuerCounts[issuer] || 0) + 1;
      });
      const sortedIssuers = Object.keys(issuerCounts).sort((a, b) => issuerCounts[b] - issuerCounts[a]);
      let issuerHtml = `<option value="">Tất cả Cơ quan (${docs.length})</option>`;
      sortedIssuers.forEach(iss => {
        issuerHtml += `<option value="${escapeHtml(iss)}">${escapeHtml(iss)} (${issuerCounts[iss]})</option>`;
      });
      ragFilterIssuer.innerHTML = issuerHtml;
      if (currentVal && issuerCounts[currentVal]) ragFilterIssuer.value = currentVal;
    }
  }

  // Tải danh mục văn bản đã duyệt trong kho
  async function loadRagDocuments() {
    if (!ragDocsTableBody) return;
    ragDocsTableBody.innerHTML = '<tr><td colspan="5" class="loading-td">Đang tải danh mục văn bản trong kho...</td></tr>';
    try {
      const res = await fetch('/api/rag/documents?limit=1000');
      if (!res.ok) throw new Error('Không thể lấy danh sách văn bản');
      const d = await res.json();
      allRagDocs = d.documents || [];

      // Cập nhật số đếm trên các Linear Filter Tabs
      const totalDocs = allRagDocs.length;
      const coreDocs = allRagDocs.filter(doc => doc.nhom_vong_doi === 'CORE_DIRECTIVE').length;
      const thematicDocs = allRagDocs.filter(doc => doc.nhom_vong_doi === 'THEMATIC_CASE').length;
      const ephemeralDocs = allRagDocs.filter(doc => doc.nhom_vong_doi === 'EPHEMERAL_EVENT').length;

      const elTotal = document.getElementById('statRagTotal');
      const elCore = document.getElementById('statRagCore');
      const elThematic = document.getElementById('statRagThematic');
      const elEphemeral = document.getElementById('statRagEphemeral');
      if (elTotal) elTotal.textContent = totalDocs;
      if (elCore) elCore.textContent = coreDocs;
      if (elThematic) elThematic.textContent = thematicDocs;
      if (elEphemeral) elEphemeral.textContent = ephemeralDocs;

      // Cập nhật các dropdown bộ lọc
      populateFilterDropdowns(allRagDocs);

      // Áp dụng bộ lọc & render bảng
      applyRagFiltersAndRender();
    } catch (err) {
      ragDocsTableBody.innerHTML = `<tr><td colspan="5" style="color:#ef4444; padding:20px;">Lỗi: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // Lọc và sắp xếp toàn bộ danh sách văn bản RAG
  function applyRagFiltersAndRender() {
    const kw = ragQuickSearch ? ragQuickSearch.value.trim().toLowerCase() : '';
    const selType = ragFilterType ? ragFilterType.value.trim().toUpperCase() : '';
    const selYear = ragFilterYear ? ragFilterYear.value.trim() : '';
    const selLifecycle = currentRagLifecycleFilter || (ragFilterLifecycle ? ragFilterLifecycle.value.trim() : '');
    const selIssuer = ragFilterIssuer ? ragFilterIssuer.value.trim() : '';

    filteredRagDocs = allRagDocs.filter(d => {
      // 1. Lọc theo từ khoá tìm kiếm tức thì
      if (kw) {
        const soHieu = (d.so_hieu_vb || '').toLowerCase();
        const trichYeu = (d.trich_yeu || '').toLowerCase();
        const coQuan = (d.co_quan_ban_hanh || '').toLowerCase();
        const nguoiKy = (d.nguoi_ky || '').toLowerCase();
        const theLoai = (d.the_loai_vb || d.the_loai || '').toLowerCase();
        const chuyenDe = (d.ten_chuyen_de || d.ma_chuyen_de || '').toLowerCase();

        const match = soHieu.includes(kw) ||
                      trichYeu.includes(kw) ||
                      coQuan.includes(kw) ||
                      nguoiKy.includes(kw) ||
                      theLoai.includes(kw) ||
                      chuyenDe.includes(kw);
        if (!match) return false;
      }

      // 2. Lọc theo Thể loại
      if (selType) {
        const t = (d.the_loai_vb || d.the_loai || '').trim().toUpperCase();
        if (t !== selType) return false;
      }

      // 3. Lọc theo Năm
      if (selYear) {
        let y = String(d.nam_ban_hanh || '');
        if (!y && d.ngay_ban_hanh) {
          const parts = String(d.ngay_ban_hanh).split(/[-\/]/);
          if (parts.length >= 3) y = parts[0].length === 4 ? parts[0] : parts[2];
        }
        if (y !== selYear) return false;
      }

      // 4. Lọc theo Vòng đời (Nền tảng / Chuyên đề / Sự vụ)
      if (selLifecycle) {
        if (d.nhom_vong_doi !== selLifecycle) return false;
      }

      // 5. Lọc theo Cơ quan
      if (selIssuer) {
        if ((d.co_quan_ban_hanh || '').trim() !== selIssuer) return false;
      }

      return true;
    });

    // Sắp xếp dữ liệu
    filteredRagDocs.sort((a, b) => {
      let valA, valB;
      if (ragSortField === 'ngay_ban_hanh') {
        valA = a.ngay_ban_hanh || '';
        valB = b.ngay_ban_hanh || '';
      } else if (ragSortField === 'so_hieu') {
        valA = a.so_hieu_vb || '';
        valB = b.so_hieu_vb || '';
      } else if (ragSortField === 'the_loai') {
        valA = a.the_loai_vb || a.the_loai || '';
        valB = b.the_loai_vb || b.the_loai || '';
      } else if (ragSortField === 'co_quan') {
        valA = a.co_quan_ban_hanh || '';
        valB = b.co_quan_ban_hanh || '';
      } else if (ragSortField === 'chunks') {
        valA = Number(a.chunk_count || 0);
        valB = Number(b.chunk_count || 0);
        return ragSortOrder === 'asc' ? valA - valB : valB - valA;
      } else {
        valA = a.ngay_ban_hanh || '';
        valB = b.ngay_ban_hanh || '';
      }

      if (ragSortOrder === 'asc') {
        return String(valA).localeCompare(String(valB), 'vi');
      } else {
        return String(valB).localeCompare(String(valA), 'vi');
      }
    });

    // Cập nhật trạng thái hiển thị số lượng
    if (ragCountVisible) ragCountVisible.textContent = filteredRagDocs.length;
    if (ragCountTotal) ragCountTotal.textContent = allRagDocs.length;
    if (ragFilterNotice) {
      if (filteredRagDocs.length !== allRagDocs.length) {
        ragFilterNotice.textContent = `(Đã lọc từ tổng số ${allRagDocs.length} văn bản trong kho)`;
      } else {
        ragFilterNotice.textContent = '';
      }
    }

    // Hiển thị nút xoá nhanh tìm kiếm
    if (btnClearQuickSearch) {
      btnClearQuickSearch.style.display = kw ? 'inline-block' : 'none';
    }

    // Đảm bảo trang hiện tại hợp lệ
    const totalPages = Math.ceil(filteredRagDocs.length / ragPageSize) || 1;
    if (currentRagPage > totalPages) currentRagPage = totalPages;
    if (currentRagPage < 1) currentRagPage = 1;

    renderRagTable();
    renderRagPagination();
  }

  // Render Dạng Bảng Phân Trang (Table View)
  function renderRagTable() {
    if (!ragDocsTableBody) return;

    if (filteredRagDocs.length === 0) {
      ragDocsTableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 40px 20px;">
            <div class="rag-empty-filter-state">
              <div class="rag-empty-filter-icon">🔍</div>
              <div class="rag-empty-filter-text">Không tìm thấy văn bản nào phù hợp với bộ lọc hiện tại.</div>
              <button type="button" class="btn-chs-outline" onclick="window.resetRagFiltersAndReload()" style="margin-top: 6px;">↺ Đặt lại bộ lọc</button>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    const startIdx = (currentRagPage - 1) * ragPageSize;
    const endIdx = startIdx + ragPageSize;
    const pageDocs = filteredRagDocs.slice(startIdx, endIdx);

    ragDocsTableBody.innerHTML = pageDocs.map(buildDocTableRowHtml).join('');
  }

  // Render Thanh Phân Trang (Pagination Bar)
  function renderRagPagination() {
    if (!ragPaginationControls || !ragPaginationInfo) return;

    const total = filteredRagDocs.length;
    if (total === 0) {
      ragPaginationInfo.textContent = 'Hiển thị 0 - 0 trong 0 văn bản';
      ragPaginationControls.innerHTML = '';
      return;
    }

    const totalPages = Math.ceil(total / ragPageSize) || 1;
    const startNum = (currentRagPage - 1) * ragPageSize + 1;
    const endNum = Math.min(currentRagPage * ragPageSize, total);

    ragPaginationInfo.innerHTML = `Hiển thị <b>${startNum} – ${endNum}</b> trong tổng số <b>${total}</b> văn bản (Trang ${currentRagPage}/${totalPages})`;

    let html = '';

    // Nút Đầu & Trước
    html += `<button type="button" class="rag-page-btn" ${currentRagPage === 1 ? 'disabled' : ''} onclick="window.changeRagPage(1)" title="Trang đầu">«</button>`;
    html += `<button type="button" class="rag-page-btn" ${currentRagPage === 1 ? 'disabled' : ''} onclick="window.changeRagPage(${currentRagPage - 1})" title="Trang trước">‹</button>`;

    // Sinh dải số trang thông minh
    const pageRange = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentRagPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
      pageRange.push(1);
      if (startPage > 2) pageRange.push('...');
    }

    for (let p = startPage; p <= endPage; p++) {
      pageRange.push(p);
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) pageRange.push('...');
      pageRange.push(totalPages);
    }

    pageRange.forEach(p => {
      if (p === '...') {
        html += `<span class="rag-page-ellipsis">…</span>`;
      } else {
        const activeClass = p === currentRagPage ? 'active' : '';
        html += `<button type="button" class="rag-page-btn ${activeClass}" onclick="window.changeRagPage(${p})">${p}</button>`;
      }
    });

    // Nút Sau & Cuối
    html += `<button type="button" class="rag-page-btn" ${currentRagPage === totalPages ? 'disabled' : ''} onclick="window.changeRagPage(${currentRagPage + 1})" title="Trang sau">›</button>`;
    html += `<button type="button" class="rag-page-btn" ${currentRagPage === totalPages ? 'disabled' : ''} onclick="window.changeRagPage(${totalPages})" title="Trang cuối">»</button>`;

    ragPaginationControls.innerHTML = html;
  }

  // Đổi trang
  window.changeRagPage = function(page) {
    const totalPages = Math.ceil(filteredRagDocs.length / ragPageSize) || 1;
    if (page < 1 || page > totalPages) return;
    currentRagPage = page;
    renderRagTable();
    renderRagPagination();

    // Cuộn nhẹ lên đầu bảng nếu đang ở xa
    if (ragDocsTableBody) {
      const rect = ragDocsTableBody.getBoundingClientRect();
      if (rect.top < 0) {
        ragDocsTableBody.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  // Render Gom nhóm Thể loại (Category Accordion View)
  function renderRagCategoryGroups() {
    if (!ragCategoryGroupsWrap) return;

    if (filteredRagDocs.length === 0) {
      ragCategoryGroupsWrap.innerHTML = `
        <div class="rag-empty-filter-state">
          <div class="rag-empty-filter-icon">📁</div>
          <div class="rag-empty-filter-text">Không có văn bản nào phù hợp với bộ lọc trong chế độ Gom nhóm Thể loại.</div>
          <button type="button" class="btn-chs-outline" onclick="window.resetRagFiltersAndReload()" style="margin-top: 6px;">↺ Đặt lại bộ lọc</button>
        </div>
      `;
      return;
    }

    // Nhóm văn bản theo thể loại
    const groups = {};
    filteredRagDocs.forEach(d => {
      const code = (d.the_loai_vb || d.the_loai || 'KHAC').trim().toUpperCase();
      if (!groups[code]) groups[code] = [];
      groups[code].push(d);
    });

    const sortedCodes = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);

    let html = '';
    sortedCodes.forEach((code, idx) => {
      const list = groups[code];
      const fullName = getTheLoaiFullName(code);
      const isExpanded = idx === 0 ? 'expanded' : ''; // Mặc định mở nhóm đầu tiên

      const coreCount = list.filter(d => d.nhom_vong_doi === 'CORE_DIRECTIVE').length;
      const thematicCount = list.length - coreCount;

      html += `
        <div class="rag-category-card ${isExpanded}" id="ragCatCard_${escapeHtml(code)}">
          <div class="rag-category-header" onclick="window.toggleRagCategoryGroup('ragCatCard_${escapeHtml(code)}')">
            <div class="rag-category-title-group">
              <span class="rag-category-icon">📁</span>
              <div>
                <span class="rag-category-name">${escapeHtml(fullName)}</span>
                <span style="font-size:12px; color:#94a3b8; margin-left:6px;">(${escapeHtml(code)})</span>
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
              <div class="rag-category-badges">
                <span class="rag-badge-count">Tổng: <b>${list.length}</b> văn bản</span>
                ${coreCount > 0 ? `<span class="badge-theloai" style="background:#ecfdf5; color:#059669; border-color:#a7f3d0;">${coreCount} Nền tảng</span>` : ''}
                ${thematicCount > 0 ? `<span class="badge-theloai" style="background:#eff6ff; color:#2563eb; border-color:#bfdbfe;">${thematicCount} Chuyên đề</span>` : ''}
              </div>
              <span class="rag-category-toggle-arrow">▼</span>
            </div>
          </div>
          <div class="rag-category-body">
            <table class="chs-table">
              <thead>
                <tr>
                  <th width="140">Số Hiệu</th>
                  <th width="150">Cơ Quan Ban Hành</th>
                  <th width="100">Ngày BH</th>
                  <th width="90">Vòng Đời</th>
                  <th width="115">Chuyên Đề</th>
                  <th>Trích Yếu Nội Dung</th>
                  <th width="70" style="text-align: center;">Chunks</th>
                  <th width="100" style="text-align: center;">Thao Tác</th>
                </tr>
              </thead>
              <tbody>
                ${list.map(d => {
                  let badgeVongDoi = '<span class="status-badge status-inprogress">Chuyên đề</span>';
                  if (d.nhom_vong_doi === 'CORE_DIRECTIVE') {
                    badgeVongDoi = '<span class="status-badge status-completed">Nền tảng</span>';
                  } else if (d.nhom_vong_doi === 'EPHEMERAL_EVENT') {
                    badgeVongDoi = '<span class="status-badge status-rescheduled">Sự vụ</span>';
                  }
                  return `
                    <tr>
                      <td><b style="color:#38bdf8;">${escapeHtml(d.so_hieu_vb || '-')}</b></td>
                      <td style="font-size:13px;">${escapeHtml(d.co_quan_ban_hanh || '-')}</td>
                      <td><code>${escapeHtml(d.ngay_ban_hanh || '-')}</code></td>
                      <td>${badgeVongDoi}</td>
                      <td><span class="badge-theloai" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; font-weight:600;">${escapeHtml(d.ten_chuyen_de || d.ma_chuyen_de || 'Chung')}</span></td>
                      <td style="max-width: 320px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${escapeHtml(d.trich_yeu || '')}">${escapeHtml(d.trich_yeu || '-')}</td>
                      <td style="text-align: center;"><span class="badge-theloai" style="background: rgba(255,255,255,0.08); color: #cbd5e1; font-weight: 600;">${d.chunk_count || 0}</span></td>
                      <td style="text-align: center; white-space: nowrap;">
                        <button class="btn-edit-doc" onclick="window.openRagDocDetail('${escapeHtml(d.doc_id)}')" title="Xem chi tiết các đoạn trích và chỉnh sửa văn bản">👁️ Sửa</button>
                        <button class="btn-delete-doc" onclick="window.deleteRagDocument('${escapeHtml(d.doc_id)}', '${escapeHtml(d.so_hieu_vb || '')}')" title="Xoá văn bản này khỏi kho">🗑️</button>
                      </td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    });

    ragCategoryGroupsWrap.innerHTML = html;
  }

  // Render Gom nhóm Năm ban hành (Year Accordion View)
  function renderRagYearGroups() {
    if (!ragYearGroupsWrap) return;

    if (filteredRagDocs.length === 0) {
      ragYearGroupsWrap.innerHTML = `
        <div class="rag-empty-filter-state">
          <div class="rag-empty-filter-icon">📅</div>
          <div class="rag-empty-filter-text">Không có văn bản nào phù hợp với bộ lọc trong chế độ Gom nhóm Năm.</div>
          <button type="button" class="btn-chs-outline" onclick="window.resetRagFiltersAndReload()" style="margin-top: 6px;">↺ Đặt lại bộ lọc</button>
        </div>
      `;
      return;
    }

    // Nhóm văn bản theo năm
    const groups = {};
    filteredRagDocs.forEach(d => {
      let y = d.nam_ban_hanh;
      if (!y && d.ngay_ban_hanh) {
        const parts = String(d.ngay_ban_hanh).split(/[-\/]/);
        if (parts.length >= 3) y = parts[0].length === 4 ? parts[0] : parts[2];
      }
      y = y || 'Chưa rõ năm';
      if (!groups[y]) groups[y] = [];
      groups[y].push(d);
    });

    const sortedYears = Object.keys(groups).sort((a, b) => {
      if (a === 'Chưa rõ năm') return 1;
      if (b === 'Chưa rõ năm') return -1;
      return Number(b) - Number(a);
    });

    let html = '';
    sortedYears.forEach((year, idx) => {
      const list = groups[year];
      const isExpanded = idx === 0 ? 'expanded' : '';

      html += `
        <div class="rag-category-card ${isExpanded}" id="ragYearCard_${escapeHtml(year)}">
          <div class="rag-category-header" onclick="window.toggleRagCategoryGroup('ragYearCard_${escapeHtml(year)}')">
            <div class="rag-category-title-group">
              <span class="rag-category-icon">📅</span>
              <span class="rag-category-name">Năm ${escapeHtml(year)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
              <span class="rag-badge-count">Tổng: <b>${list.length}</b> văn bản</span>
              <span class="rag-category-toggle-arrow">▼</span>
            </div>
          </div>
          <div class="rag-category-body">
            <table class="chs-table">
              <thead>
                <tr>
                  <th width="140">Số Hiệu</th>
                  <th width="90">Thể Loại</th>
                  <th width="150">Cơ Quan Ban Hành</th>
                  <th width="100">Ngày BH</th>
                  <th width="90">Vòng Đời</th>
                  <th width="115">Chuyên Đề</th>
                  <th>Trích Yếu Nội Dung</th>
                  <th width="70" style="text-align: center;">Chunks</th>
                  <th width="100" style="text-align: center;">Thao Tác</th>
                </tr>
              </thead>
              <tbody>
                ${list.map(buildDocTableRowHtml).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    });

    ragYearGroupsWrap.innerHTML = html;
  }

  // Helper toggle Accordion Group
  window.toggleRagCategoryGroup = function(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;
    card.classList.toggle('expanded');
  };

  // Helper đặt lại bộ lọc
  window.resetRagFiltersAndReload = function() {
    if (ragQuickSearch) ragQuickSearch.value = '';
    if (ragFilterType) ragFilterType.value = '';
    if (ragFilterYear) ragFilterYear.value = '';
    if (ragFilterLifecycle) ragFilterLifecycle.value = '';
    if (ragFilterIssuer) ragFilterIssuer.value = '';
    if (ragSortSelect) ragSortSelect.value = 'ngay_ban_hanh_desc';
    ragSortField = 'ngay_ban_hanh';
    ragSortOrder = 'desc';
    currentRagPage = 1;
    applyRagFiltersAndRender();
  };

  // Gắn sự kiện Chuyển đổi Chế độ Xem (View Switcher)
  if (ragViewSwitcher) {
    const viewButtons = ragViewSwitcher.querySelectorAll('.rag-view-btn');
    viewButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetView = btn.getAttribute('data-view');
        if (!targetView || targetView === currentRagView) return;

        viewButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentRagView = targetView;

        if (ragTableView) ragTableView.style.display = targetView === 'table' ? 'block' : 'none';
        if (ragCategoryView) ragCategoryView.style.display = targetView === 'category' ? 'block' : 'none';
        if (ragYearView) ragYearView.style.display = targetView === 'year' ? 'block' : 'none';

        applyRagFiltersAndRender();
      });
    });
  }

  // Gắn sự kiện Tìm kiếm Tức thì (Realtime Quick Search)
  if (ragQuickSearch) {
    ragQuickSearch.addEventListener('input', () => {
      clearTimeout(ragSearchDebounceTimer);
      ragSearchDebounceTimer = setTimeout(() => {
        currentRagPage = 1;
        applyRagFiltersAndRender();
      }, 200);
    });
  }

  if (btnClearQuickSearch) {
    btnClearQuickSearch.addEventListener('click', () => {
      if (ragQuickSearch) {
        ragQuickSearch.value = '';
        ragQuickSearch.focus();
      }
      currentRagPage = 1;
      applyRagFiltersAndRender();
    });
  }

  // Gắn sự kiện thay đổi các Dropdown bộ lọc
  if (ragFilterType) ragFilterType.addEventListener('change', () => { currentRagPage = 1; applyRagFiltersAndRender(); });
  if (ragFilterYear) ragFilterYear.addEventListener('change', () => { currentRagPage = 1; applyRagFiltersAndRender(); });
  if (ragFilterLifecycle) ragFilterLifecycle.addEventListener('change', () => { currentRagPage = 1; applyRagFiltersAndRender(); });
  if (ragFilterIssuer) ragFilterIssuer.addEventListener('change', () => { currentRagPage = 1; applyRagFiltersAndRender(); });

  // Gắn sự kiện đặt lại bộ lọc
  if (btnResetRagFilters) {
    btnResetRagFilters.addEventListener('click', window.resetRagFiltersAndReload);
  }

  // Gắn sự kiện số lượng bản ghi mỗi trang
  if (ragPageSizeSelect) {
    ragPageSizeSelect.addEventListener('change', () => {
      ragPageSize = parseInt(ragPageSizeSelect.value, 10) || 15;
      currentRagPage = 1;
      applyRagFiltersAndRender();
    });
  }

  // Gắn sự kiện Sắp xếp từ Dropdown
  if (ragSortSelect) {
    ragSortSelect.addEventListener('change', () => {
      const val = ragSortSelect.value;
      if (val === 'ngay_ban_hanh_desc') { ragSortField = 'ngay_ban_hanh'; ragSortOrder = 'desc'; }
      else if (val === 'ngay_ban_hanh_asc') { ragSortField = 'ngay_ban_hanh'; ragSortOrder = 'asc'; }
      else if (val === 'so_hieu_asc') { ragSortField = 'so_hieu'; ragSortOrder = 'asc'; }
      else if (val === 'chunks_desc') { ragSortField = 'chunks'; ragSortOrder = 'desc'; }

      updateSortableHeadersUI();
      applyRagFiltersAndRender();
    });
  }

  // Gắn sự kiện Click sắp xếp trên Tiêu đề cột Table
  function updateSortableHeadersUI() {
    const headers = document.querySelectorAll('.chs-table th.sortable-th');
    headers.forEach(th => {
      const sortKey = th.getAttribute('data-sort');
      const icon = th.querySelector('.sort-icon');
      if (sortKey === ragSortField) {
        th.classList.add('active-sort');
        if (icon) icon.textContent = ragSortOrder === 'asc' ? '▲' : '▼';
      } else {
        th.classList.remove('active-sort');
        if (icon) icon.textContent = '↕';
      }
    });
  }

  const sortableHeaders = document.querySelectorAll('.chs-table th.sortable-th');
  sortableHeaders.forEach(th => {
    th.addEventListener('click', () => {
      const sortKey = th.getAttribute('data-sort');
      if (!sortKey) return;

      if (ragSortField === sortKey) {
        ragSortOrder = ragSortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        ragSortField = sortKey;
        ragSortOrder = (sortKey === 'ngay_ban_hanh' || sortKey === 'chunks') ? 'desc' : 'asc';
      }

      updateSortableHeadersUI();
      applyRagFiltersAndRender();
    });
  });

  // Gắn sự kiện Toggle FTS5 Tra cứu toàn văn Panel
  if (btnToggleFtsWrap && ragFtsPanel) {
    btnToggleFtsWrap.addEventListener('click', () => {
      const isVisible = ragFtsPanel.style.display !== 'none';
      ragFtsPanel.style.display = isVisible ? 'none' : 'block';
      if (!isVisible && ragSearchInput) ragSearchInput.focus();
    });
  }

  if (btnCloseFtsPanel && ragFtsPanel) {
    btnCloseFtsPanel.addEventListener('click', () => {
      ragFtsPanel.style.display = 'none';
    });
  }

  // Mở/Thu gọn tất cả nhóm Thể loại
  if (btnExpandAllCats) {
    btnExpandAllCats.addEventListener('click', () => {
      const cards = document.querySelectorAll('#ragCategoryGroupsWrap .rag-category-card');
      cards.forEach(c => c.classList.add('expanded'));
    });
  }
  if (btnCollapseAllCats) {
    btnCollapseAllCats.addEventListener('click', () => {
      const cards = document.querySelectorAll('#ragCategoryGroupsWrap .rag-category-card');
      cards.forEach(c => c.classList.remove('expanded'));
    });
  }

  // Mở/Thu gọn tất cả nhóm Năm
  if (btnExpandAllYears) {
    btnExpandAllYears.addEventListener('click', () => {
      const cards = document.querySelectorAll('#ragYearGroupsWrap .rag-category-card');
      cards.forEach(c => c.classList.add('expanded'));
    });
  }
  if (btnCollapseAllYears) {
    btnCollapseAllYears.addEventListener('click', () => {
      const cards = document.querySelectorAll('#ragYearGroupsWrap .rag-category-card');
      cards.forEach(c => c.classList.remove('expanded'));
    });
  }

  // --- MODAL CHI TIẾT & CHỈNH SỬA VĂN BẢN (READ & UPDATE) ---
  const modalRagDetail = document.getElementById('modalRagDetail');
  const btnCloseEditModal = document.getElementById('btnCloseEditModal');
  const btnCancelEditModal = document.getElementById('btnCancelEditModal');
  const btnSaveDocEdit = document.getElementById('btnSaveDocEdit');

  const editDocId = document.getElementById('editDocId');
  const editSoHieu = document.getElementById('editSoHieu');
  const editNgay = document.getElementById('editNgay');
  const editCoQuan = document.getElementById('editCoQuan');
  const editTheLoai = document.getElementById('editTheLoai');
  const editVongDoi = document.getElementById('editVongDoi');
  const editChuyenDe = document.getElementById('editChuyenDe');
  const editHieuLuc = document.getElementById('editHieuLuc');
  const editThayTheBoi = document.getElementById('editThayTheBoi');
  const editTrichYeu = document.getElementById('editTrichYeu');
  const editChunksList = document.getElementById('editChunksList');
  const editCitationsList = document.getElementById('editCitationsList');
  const editChunksTitle = document.getElementById('editChunksTitle');

  // Hàm mở Modal Chi tiết & Chỉnh sửa văn bản (Read & Update)
  window.openRagDocDetail = async function(docId) {
    try {
      const res = await fetch(`/api/rag/documents/${encodeURIComponent(docId)}`);
      if (!res.ok) throw new Error('Không thể tải chi tiết văn bản');
      const data = await res.json();
      const doc = data.document;

      if (!doc) return;

      // Đổ dữ liệu vào form
      if (editDocId) editDocId.value = doc.doc_id || '';
      if (editSoHieu) editSoHieu.value = doc.so_hieu_vb || '';
      if (editNgay) editNgay.value = doc.ngay_ban_hanh || '';
      if (editCoQuan) editCoQuan.value = doc.co_quan_ban_hanh || '';
      if (editTheLoai) editTheLoai.value = doc.the_loai_vb || 'BC';
      if (editVongDoi) editVongDoi.value = doc.nhom_vong_doi || 'THEMATIC_CASE';
      if (editHieuLuc) editHieuLuc.value = doc.trang_thai_hieu_luc || 'CON_HIEU_LUC';
      if (editThayTheBoi) editThayTheBoi.value = doc.bi_thay_the_boi_so_hieu || '';
      if (editTrichYeu) editTrichYeu.value = doc.trich_yeu || '';

      // Tải danh mục chuyên đề vào select của Edit modal
      if (editChuyenDe) {
        const resThematics = await fetch('/api/rag/thematics');
        if (resThematics.ok) {
          const tData = await resThematics.json();
          editChuyenDe.innerHTML = (tData.thematics || []).map(c => 
            `<option value="${escapeHtml(c.ma_chuyen_de)}">${escapeHtml(c.ten_chuyen_de)}</option>`
          ).join('');
          editChuyenDe.value = doc.ma_chuyen_de || 'VAN_PHONG_THI_DUA';
        }
      }

      // Render danh sách chunks
      const chunks = doc.chunks || [];
      if (editChunksTitle) editChunksTitle.textContent = `Danh sách các đoạn trích trong CSDL (${chunks.length} đoạn chunks):`;
      if (editChunksList) {
        if (chunks.length === 0) {
          editChunksList.innerHTML = '<div style="color:#94a3b8; font-size:12px;">Văn bản này chưa có đoạn trích chunks nào.</div>';
        } else {
          editChunksList.innerHTML = chunks.map((c, idx) => `
            <div class="chunk-preview-box">
              <div style="font-weight:700; color:#38bdf8; margin-bottom:3px;">
                Đoạn ${idx + 1}: ${escapeHtml(c.section_path || 'Nội dung chung')} (${escapeHtml(c.sub_doc_owner || 'Tập thể')})
              </div>
              <div>${escapeHtml(c.chunk_text || '')}</div>
            </div>
          `).join('');
        }
      }

      // Render đồ thị liên kết
      const citations = doc.citations || [];
      if (editCitationsList) {
        if (citations.length === 0) {
          editCitationsList.innerHTML = '<div style="color:#94a3b8; font-size:12px;">Chưa ghi nhận liên kết căn cứ với văn bản khác.</div>';
        } else {
          editCitationsList.innerHTML = citations.map(cit => `
            <div style="padding: 6px 10px; background: #1e293b; border-radius: 6px; border-left: 3px solid #10b981;">
              • <b>${escapeHtml(cit.vb_dich_so_hieu)}</b>: <i style="color:#94a3b8;">${escapeHtml(cit.ghi_chu_quan_he || cit.loai_quan_he)}</i>
            </div>
          `).join('');
        }
      }

      // Mở modal
      if (modalRagDetail) modalRagDetail.style.display = 'flex';
    } catch (err) {
      showToast('Lỗi tải chi tiết văn bản: ' + err.message, 'error');
    }
  };

  // Đóng modal Edit
  function closeEditModal() {
    if (modalRagDetail) modalRagDetail.style.display = 'none';
  }
  if (btnCloseEditModal) btnCloseEditModal.addEventListener('click', closeEditModal);
  if (btnCancelEditModal) btnCancelEditModal.addEventListener('click', closeEditModal);

  // Lưu chỉnh sửa văn bản (Update)
  if (btnSaveDocEdit) {
    btnSaveDocEdit.addEventListener('click', async () => {
      const docId = editDocId ? editDocId.value : '';
      if (!docId) return;

      const soHieu = editSoHieu ? editSoHieu.value.trim() : '';
      const trichYeu = editTrichYeu ? editTrichYeu.value.trim() : '';
      if (!soHieu) {
        showToast('Số hiệu văn bản không được để trống!', 'warning');
        return;
      }
      if (!trichYeu) {
        showToast('Trích yếu không được để trống!', 'warning');
        return;
      }

      const updates = {
        so_hieu_vb: soHieu,
        ngay_ban_hanh: editNgay ? editNgay.value : '',
        co_quan_ban_hanh: editCoQuan ? editCoQuan.value.trim() : '',
        the_loai_vb: editTheLoai ? editTheLoai.value : 'BC',
        nhom_vong_doi: editVongDoi ? editVongDoi.value : 'THEMATIC_CASE',
        ma_chuyen_de: editChuyenDe ? editChuyenDe.value : 'VAN_PHONG_THI_DUA',
        trang_thai_hieu_luc: editHieuLuc ? editHieuLuc.value : 'CON_HIEU_LUC',
        bi_thay_the_boi_so_hieu: editThayTheBoi ? editThayTheBoi.value.trim() : '',
        trich_yeu: trichYeu
      };

      try {
        btnSaveDocEdit.disabled = true;
        btnSaveDocEdit.textContent = '⏳ Đang lưu cập nhật...';

        const res = await fetch(`/api/rag/documents/${encodeURIComponent(docId)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates)
        });

        const data = await res.json();
        if (res.ok) {
          showToast(`✓ Đã cập nhật thành công thông tin văn bản "${updates.so_hieu_vb}"!`, 'success');
          closeEditModal();
          loadRagDocuments();
          loadRagStats();
        } else {
          showToast('Lỗi cập nhật: ' + (data.detail || 'Lỗi server'), 'error');
        }
      } catch (err) {
        showToast('Lỗi kết nối: ' + err.message, 'error');
      } finally {
        btnSaveDocEdit.disabled = false;
        btnSaveDocEdit.textContent = '💾 Lưu chỉnh sửa văn bản';
      }
    });
  }

  // 3. Xoá từng văn bản
  window.deleteRagDocument = async function(docId, soHieu) {
    const confirmMsg = `Đồng chí có chắc chắn muốn xoá văn bản "${soHieu || docId}" cùng toàn bộ các đoạn trích liên quan khỏi Kho RAG?`;
    if (!confirm(confirmMsg)) return;

    try {
      const res = await fetch(`/api/rag/documents/${encodeURIComponent(docId)}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || '✓ Đã xoá văn bản thành công!', 'success');
        loadRagStats();
        loadRagDocuments();
      } else {
        showToast('Lỗi: ' + (data.detail || 'Không thể xoá văn bản'), 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng khi xoá văn bản: ' + err.message, 'error');
    }
  };

  // 4. Xoá sạch toàn bộ kho RAG
  if (btnClearRag) {
    btnClearRag.addEventListener('click', async () => {
      const confirm1 = confirm('⚠️ CẢNH BÁO: Thao tác này sẽ xoá TOÀN BỘ dữ liệu RAG (sổ văn bản, đoạn trích chunks, chỉ mục tìm kiếm FTS5, liên kết trích dẫn) để chuẩn bị nạp lại từ đầu.\n\nĐồng chí có chắc chắn muốn xoá sạch?');
      if (!confirm1) return;

      const confirm2 = confirm('Xác nhận lần 2: Dữ liệu văn bản RAG sẽ bị làm trống hoàn toàn. Tiếp tục?');
      if (!confirm2) return;

      try {
        btnClearRag.disabled = true;
        btnClearRag.textContent = '⏳ Đang xoá sạch...';
        const res = await fetch('/api/rag/clear', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          showToast('✓ Đã xoá sạch toàn bộ dữ liệu Kho RAG thành công!', 'success');
          loadRagStats();
          loadRagDocuments();
          if (ragResultsWrap) ragResultsWrap.innerHTML = '';
        } else {
          showToast('Lỗi xoá dữ liệu: ' + (data.detail || 'Lỗi server'), 'error');
        }
      } catch (err) {
        showToast('Lỗi kết nối: ' + err.message, 'error');
      } finally {
        btnClearRag.disabled = false;
        btnClearRag.innerHTML = '🗑️ Xoá sạch kho RAG';
      }
    });
  }

  // 5. Nạp văn bản mới & Chế độ Kéo Thả (Drag & Drop Zone)
  const ragDropZone = document.getElementById('ragDropZone');
  const ragDropLoading = document.getElementById('ragDropLoading');
  const btnBrowseDropzone = document.getElementById('btnBrowseDropzone');

  // Hàm xử lý tệp nạp vào Kho RAG (Preview -> Modal Kiểm Duyệt)
  window.processRagFileForPreview = async function(file) {
    if (!file) return;

    // Kiểm tra định dạng đuôi tệp
    const fileName = file.name.toLowerCase();
    const validExts = ['.docx', '.doc', '.pdf', '.txt', '.md'];
    const isValid = validExts.some(ext => fileName.endsWith(ext));
    if (!isValid) {
      showToast(`Định dạng tệp "${file.name}" không được hỗ trợ (chỉ nhận Word, PDF, Text).`, 'warning');
      return;
    }

    const originalBtnText = btnUploadForRag ? btnUploadForRag.innerHTML : '';
    if (btnUploadForRag) {
      btnUploadForRag.disabled = true;
      btnUploadForRag.innerHTML = '⏳ Đang phân tích văn bản...';
    }
    if (ragDropLoading) ragDropLoading.style.display = 'flex';

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/rag/preview', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        showToast('⚠️ Không thể tiếp nhận văn bản: ' + (data.detail || 'Lỗi không xác định'), 'error');
        return;
      }

      // Lưu preview data vào biến toàn cục phiên
      const preview = data.preview || data;
      currentRagPreviewData = preview;

      // Điền dữ liệu bóc tách vào Modal
      if (reviewFileNotice) {
        reviewFileNotice.textContent = `Tệp: "${escapeHtml(preview.file_name || preview.file_path || file.name)}" — Đã bóc tách ${preview.file_size_kb || 0} KB, dự kiến tạo ${preview.estimated_chunks || 0} đoạn trích (chunks).`;
      }
      if (reviewSoHieu) reviewSoHieu.value = preview.so_hieu_vb || '';
      if (reviewNgay) reviewNgay.value = preview.ngay_ban_hanh || '';
      if (reviewCoQuan) reviewCoQuan.value = preview.co_quan_ban_hanh || 'Đảng uỷ xã Công Hải';
      if (reviewCoQuanCode) reviewCoQuanCode.value = preview.co_quan_ban_hanh_code || 'DU';
      if (reviewTheLoai) reviewTheLoai.value = preview.the_loai_vb || 'BC';
      if (reviewVongDoi) reviewVongDoi.value = preview.nhom_vong_doi || 'THEMATIC_CASE';
      if (reviewTrichYeu) reviewTrichYeu.value = preview.trich_yeu || '';
      if (reviewThayThe) reviewThayThe.value = preview.thay_the_so_hieu || '';

      // Tải danh mục chuyên đề và chọn chuyên đề AI vừa phát hiện
      if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'none';
      await loadThematics(preview.ma_chuyen_de || 'VAN_PHONG_THI_DUA');

      // Hiển thị danh sách chunks preview
      if (reviewChunksPreview) {
        const chunks = preview.preview_chunks || [];
        if (chunks.length === 0) {
          reviewChunksPreview.innerHTML = '<div style="color:#94a3b8; font-size:12px;">Đang chuẩn bị cắt đoạn trích khi phê duyệt.</div>';
        } else {
          reviewChunksPreview.innerHTML = chunks.map((c, idx) => `
            <div class="chunk-preview-box">
              <div style="font-weight:700; color:#38bdf8; margin-bottom:3px;">
                Đoạn ${idx + 1}: ${escapeHtml(c.section_path || 'Nội dung chung')} (${escapeHtml(c.sub_doc_owner || 'Tập thể')})
              </div>
              <div>${escapeHtml((c.chunk_text || '').substring(0, 180))}...</div>
            </div>
          `).join('');
        }
      }

      // Mở Modal kiểm duyệt (Human-in-the-Loop)
      if (modalRagReview) modalRagReview.style.display = 'flex';
    } catch (err) {
      showToast('Lỗi khi đọc và bóc tách tệp: ' + err.message, 'error');
    } finally {
      if (btnUploadForRag) {
        btnUploadForRag.disabled = false;
        btnUploadForRag.innerHTML = originalBtnText;
      }
      if (ragDropLoading) ragDropLoading.style.display = 'none';
    }
  };

  // Nút Nạp trên thanh điều khiển
  if (btnUploadForRag && ragFileInput) {
    btnUploadForRag.addEventListener('click', () => {
      ragFileInput.value = '';
      ragFileInput.click();
    });
  }

  // Nút Chọn tệp trên Khung Kéo Thả
  if (btnBrowseDropzone && ragFileInput) {
    btnBrowseDropzone.addEventListener('click', (e) => {
      e.stopPropagation(); // Không trigger click vào ragDropZone
      ragFileInput.value = '';
      ragFileInput.click();
    });
  }

  // Click vào vùng Khung Kéo Thả
  if (ragDropZone && ragFileInput) {
    ragDropZone.addEventListener('click', () => {
      ragFileInput.value = '';
      ragFileInput.click();
    });

    // Kéo thả trực tiếp vào Khung Dropzone
    ragDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      ragDropZone.classList.add('drag-active');
    });

    ragDropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      ragDropZone.classList.remove('drag-active');
    });

    ragDropZone.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      ragDropZone.classList.remove('drag-active');

      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        await window.processRagFileForPreview(files[0]);
      }
    });
  }

  // Khi chọn file từ hộp thoại máy tính
  if (ragFileInput) {
    ragFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) {
        await window.processRagFileForPreview(file);
      }
    });
  }

  // 6. Đóng Modal Kiểm duyệt
  function closeRagModal() {
    if (modalRagReview) modalRagReview.style.display = 'none';
    currentRagPreviewData = null;
    if (ragFileInput) ragFileInput.value = '';
    if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'none';
  }

  if (btnCloseRagModal) btnCloseRagModal.addEventListener('click', closeRagModal);
  if (btnCancelRagReview) btnCancelRagReview.addEventListener('click', closeRagModal);

  // 7. Cán bộ Phê duyệt & Nạp chính thức vào Kho RAG
  if (btnCommitRag) {
    btnCommitRag.addEventListener('click', async () => {
      if (!currentRagPreviewData) {
        showToast('Không có dữ liệu văn bản để nạp!', 'warning');
        return;
      }

      const soHieu = reviewSoHieu ? reviewSoHieu.value.trim() : '';
      const ngay = reviewNgay ? reviewNgay.value : '';
      const coQuan = reviewCoQuan ? reviewCoQuan.value.trim() : '';
      const trichYeu = reviewTrichYeu ? reviewTrichYeu.value.trim() : '';

      if (!soHieu) {
        showToast('Vui lòng nhập Số hiệu văn bản!', 'warning');
        if (reviewSoHieu) reviewSoHieu.focus();
        return;
      }
      if (!ngay) {
        showToast('Vui lòng chọn Ngày ban hành văn bản!', 'warning');
        if (reviewNgay) reviewNgay.focus();
        return;
      }
      if (!coQuan) {
        showToast('Vui lòng nhập Cơ quan ban hành!', 'warning');
        if (reviewCoQuan) reviewCoQuan.focus();
        return;
      }
      if (!trichYeu) {
        showToast('Vui lòng nhập Trích yếu nội dung văn bản!', 'warning');
        if (reviewTrichYeu) reviewTrichYeu.focus();
        return;
      }

      // Xử lý chuyên đề
      let maChuyenDe = reviewChuyenDe ? reviewChuyenDe.value : 'VAN_PHONG_THI_DUA';
      if (maChuyenDe === '__NEW__') {
        const customName = inputNewChuyenDe ? inputNewChuyenDe.value.trim() : '';
        if (customName) {
          try {
            const resCat = await fetch('/api/rag/thematics', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ten_chuyen_de: customName })
            });
            if (resCat.ok) {
              const dataCat = await resCat.json();
              maChuyenDe = dataCat.thematic.ma_chuyen_de;
            }
          } catch (e) {
            console.warn('Lỗi tự động lưu chuyên đề:', e);
          }
        } else {
          maChuyenDe = 'VAN_PHONG_THI_DUA';
        }
      }

      // Xây dựng payload đã kiểm duyệt
      const payload = {
        file_path: currentRagPreviewData.file_path || '',
        so_hieu_vb: soHieu,
        ngay_ban_hanh: ngay,
        co_quan_ban_hanh: coQuan,
        co_quan_ban_hanh_code: reviewCoQuanCode ? reviewCoQuanCode.value : 'DU',
        the_loai_vb: reviewTheLoai ? reviewTheLoai.value : 'BC',
        nhom_vong_doi: reviewVongDoi ? reviewVongDoi.value : 'THEMATIC_CASE',
        ma_chuyen_de: maChuyenDe,
        trich_yeu: trichYeu,
        thay_the_so_hieu: (reviewThayThe && reviewThayThe.value.trim()) ? reviewThayThe.value.trim() : '',
        full_text: currentRagPreviewData.full_text || '',
        citations: currentRagPreviewData.citations || []
      };

      try {
        btnCommitRag.disabled = true;
        btnCommitRag.textContent = '⏳ Đang lưu vào Kho RAG...';

        const res = await fetch('/api/rag/commit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
          const chunkCount = (data.data && data.data.chunks) || 'nhiều';
          showToast(`✓ Phê duyệt và nạp văn bản "${payload.so_hieu_vb}" vào Kho RAG thành công! (${chunkCount} đoạn trích)`, 'success');
          closeRagModal();
          loadRagStats();
          loadRagDocuments();
        } else {
          showToast('⚠️ Lỗi khi lưu văn bản: ' + (data.detail || 'Lỗi hệ thống'), 'error');
        }
      } catch (err) {
        showToast('Lỗi kết nối khi lưu: ' + err.message, 'error');
      } finally {
        btnCommitRag.disabled = false;
        btnCommitRag.innerHTML = '✓ Phê duyệt & Nạp vào Kho RAG';
      }
    });
  }

  // 8. Làm mới danh mục văn bản
  if (btnRefreshRagDocs) {
    btnRefreshRagDocs.addEventListener('click', () => {
      loadRagStats();
      loadRagDocuments();
    });
  }

  // 9. Tra cứu đối soát FTS5 BM25
  if (btnRagSearch) btnRagSearch.addEventListener('click', searchRag);
  if (ragSearchInput) {
    ragSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') searchRag();
    });
  }

  async function searchRag() {
    const q = ragSearchInput ? ragSearchInput.value.trim() : '';
    if (!q) return;
    ragResultsWrap.innerHTML = '<div class="loading-state">Đang tra cứu siêu tốc FTS5 BM25...</div>';

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const results = data.results || [];

      if (results.length === 0) {
        ragResultsWrap.innerHTML = `<div class="empty-state">Không tìm thấy đoạn trích nào chứa từ khoá: "<b>${escapeHtml(q)}</b>".</div>`;
        return;
      }

      ragResultsWrap.innerHTML = results.map((r, idx) => `
        <div class="rag-item">
          <div class="rag-header">
            <span class="rag-sohieu">${escapeHtml(r.so_hieu_vb || 'Văn bản')}</span>
            <span>Ngày: ${escapeHtml(r.ngay_ban_hanh || '2026')} | Tầng: <b>${escapeHtml(r.nhom_vong_doi || 'THEMATIC')}</b></span>
          </div>
          <div style="font-size:13.5px; font-weight:600; color:#f8fafc;">${escapeHtml(r.trich_yeu || '')}</div>
          <div class="rag-snippet">${escapeHtml(r.chunk_text || '')}</div>
        </div>
      `).join('');
    } catch (err) {
      ragResultsWrap.innerHTML = `<div style="color:#ef4444; padding:20px;">Lỗi tìm kiếm: ${escapeHtml(err.message)}</div>`;
    }
  }

  // --- DANH BẠ HỆ THỐNG ---
  const directoryGrid = document.getElementById('directoryGrid');

  async function loadDirectory() {
    if (!directoryGrid) return;
    directoryGrid.innerHTML = '<div class="loading-state">Đang tải danh bạ cán bộ & chi bộ...</div>';

    try {
      const res = await fetch('/api/directory');
      const data = await res.json();
      const dir = data.directory || [];

      directoryGrid.innerHTML = dir.map(cb => `
        <div class="dir-card">
          <div class="dir-name">${escapeHtml(cb.ho_ten)}</div>
          <div class="dir-role">${escapeHtml(cb.chuc_vu)}</div>
          <div class="dir-unit">Đơn vị: <b>${escapeHtml(cb.co_quan)}</b></div>
          ${cb.so_dien_thoai ? `<div style="font-size:12px; color:#64748b;">ĐT: ${escapeHtml(cb.so_dien_thoai)}</div>` : ''}
        </div>
      `).join('');
    } catch (err) {
      directoryGrid.innerHTML = `<div style="color:#ef4444; padding:20px;">Lỗi tải danh bạ: ${escapeHtml(err.message)}</div>`;
    }
  }

  // ============================================================================
  // 8. ĐĂNG NHẬP SĐT ZALO & BẢNG ĐIỀU HÀNH ADMIN TOÀN DIỆN
  // ============================================================================
  const btnAuthTrigger = document.getElementById('btnAuthTrigger');
  const authBadgeIcon = document.getElementById('authBadgeIcon');
  const authBadgeName = document.getElementById('authBadgeName');
  const authBadgeSub = document.getElementById('authBadgeSub');
  const tabNavAdmin = document.getElementById('tabNavAdmin');

  const modalAuth = document.getElementById('modalAuth');
  const btnCloseAuthModal = document.getElementById('btnCloseAuthModal');

  const authStep1 = document.getElementById('authStep1');
  const inputAuthPhone = document.getElementById('inputAuthPhone');
  const authNoticePhone = document.getElementById('authNoticePhone');
  const btnSendOtp = document.getElementById('btnSendOtp');

  const authStep2 = document.getElementById('authStep2');
  const displayAuthTargetPhone = document.getElementById('displayAuthTargetPhone');
  const inputAuthOtp = document.getElementById('inputAuthOtp');
  const authNoticeOtp = document.getElementById('authNoticeOtp');
  const authDevOtpHint = document.getElementById('authDevOtpHint');
  const btnVerifyOtp = document.getElementById('btnVerifyOtp');
  const btnBackToStep1 = document.getElementById('btnBackToStep1');

  const authStepProfile = document.getElementById('authStepProfile');
  const profileName = document.getElementById('profileName');
  const profileRole = document.getElementById('profileRole');
  const profilePhone = document.getElementById('profilePhone');
  const profileAdminBadge = document.getElementById('profileAdminBadge');
  const btnGoToAdminFromModal = document.getElementById('btnGoToAdminFromModal');
  const btnLogout = document.getElementById('btnLogout');

  let currentAuthTargetPhone = '';
  let currentCadre = null;

  async function checkAuthSession() {
    try {
      const token = localStorage.getItem('cva_auth_token') || '';
      const res = await fetch('/api/auth/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token, session_id: sessionId })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.can_bo) {
          applyCadreLogin(data.can_bo, token);
          return;
        }
      }
      applyGuestMode();
    } catch {
      applyGuestMode();
    }
  }

  function applyCadreLogin(cb, token) {
    currentCadre = cb;
    if (token) localStorage.setItem('cva_auth_token', token);
    localStorage.setItem('cva_can_bo_info', JSON.stringify(cb));

    if (authBadgeName) authBadgeName.textContent = cb.ho_ten;
    if (authBadgeIcon) authBadgeIcon.textContent = cb.vai_tro === 'admin' ? '👑' : '👤';
    if (btnAuthTrigger) btnAuthTrigger.className = 'btn-auth-badge ' + (cb.vai_tro === 'admin' ? 'admin' : 'authenticated');
    if (welcomeUserName) welcomeUserName.textContent = 'đồng chí ' + cb.ho_ten;

    if (cb.vai_tro === 'admin') {
      if (adminSwitchBar) adminSwitchBar.style.display = 'flex';
      if (profileAdminBadge) profileAdminBadge.style.display = 'inline-block';
      if (btnGoToAdminFromModal) btnGoToAdminFromModal.style.display = 'block';
    } else {
      if (adminSwitchBar) adminSwitchBar.style.display = 'none';
      if (profileAdminBadge) profileAdminBadge.style.display = 'none';
      if (btnGoToAdminFromModal) btnGoToAdminFromModal.style.display = 'none';
      showView('chat');
    }
  }

  function applyGuestMode() {
    currentCadre = null;
    localStorage.removeItem('cva_auth_token');
    localStorage.removeItem('cva_can_bo_info');

    if (authBadgeName) authBadgeName.textContent = 'Chế độ Khách';
    if (authBadgeIcon) authBadgeIcon.textContent = '🕶️';
    if (btnAuthTrigger) btnAuthTrigger.className = 'btn-auth-badge guest';
    if (welcomeUserName) welcomeUserName.textContent = 'đồng chí';

    if (adminSwitchBar) adminSwitchBar.style.display = 'none';
    if (profileAdminBadge) profileAdminBadge.style.display = 'none';
    if (btnGoToAdminFromModal) btnGoToAdminFromModal.style.display = 'none';
    showView('chat');
  }

  if (btnAuthTrigger) {
    btnAuthTrigger.addEventListener('click', () => {
      if (currentCadre) {
        if (profileName) profileName.textContent = currentCadre.ho_ten;
        if (profileRole) profileRole.textContent = `${currentCadre.chuc_vu} — ${currentCadre.co_quan}`;
        if (profilePhone) profilePhone.textContent = `Số điện thoại: ${currentCadre.so_dien_thoai || 'Chưa cập nhật'}`;
        if (authStep1) authStep1.style.display = 'none';
        if (authStep2) authStep2.style.display = 'none';
        if (authStepProfile) authStepProfile.style.display = 'block';
      } else {
        if (authStep1) authStep1.style.display = 'block';
        if (authStep2) authStep2.style.display = 'none';
        if (authStepProfile) authStepProfile.style.display = 'none';
        if (inputAuthPhone) {
          inputAuthPhone.value = '';
          setTimeout(() => inputAuthPhone.focus(), 100);
        }
        if (authNoticePhone) authNoticePhone.textContent = '';
      }
      if (modalAuth) modalAuth.style.display = 'flex';
    });
  }

  if (btnCloseAuthModal) {
    btnCloseAuthModal.addEventListener('click', () => {
      if (modalAuth) modalAuth.style.display = 'none';
    });
  }

  const btnResendOtp = document.getElementById('btnResendOtp');
  let resendCountdownTimer = null;

  function startResendCountdown(seconds = 60) {
    if (!btnResendOtp) return;
    if (resendCountdownTimer) clearInterval(resendCountdownTimer);
    let remaining = seconds;
    btnResendOtp.disabled = true;
    btnResendOtp.style.opacity = '0.5';
    btnResendOtp.style.cursor = 'not-allowed';
    btnResendOtp.textContent = `Gửi lại mã (${remaining}s)`;

    resendCountdownTimer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(resendCountdownTimer);
        btnResendOtp.disabled = false;
        btnResendOtp.style.opacity = '1';
        btnResendOtp.style.cursor = 'pointer';
        btnResendOtp.textContent = 'Gửi lại mã OTP';
      } else {
        btnResendOtp.textContent = `Gửi lại mã (${remaining}s)`;
      }
    }, 1000);
  }

  async function triggerSendOtp(phone) {
    const res = await fetch('/api/auth/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: phone })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Không thể tạo mã xác thực');
    }

    currentAuthTargetPhone = phone;
    if (displayAuthTargetPhone) {
      displayAuthTargetPhone.textContent = data.phone_masked || phone;
    }
    
    // Xoá trắng ô nhập OTP, bắt buộc cán bộ mở Zalo trên điện thoại lấy mã thực tế
    if (inputAuthOtp) inputAuthOtp.value = '';

    authStep1.style.display = 'none';
    authStep2.style.display = 'block';
    if (inputAuthOtp) inputAuthOtp.focus();
    startResendCountdown(60);
  }

  if (btnSendOtp && inputAuthPhone) {
    btnSendOtp.addEventListener('click', async () => {
      const phone = inputAuthPhone.value.trim();
      if (!phone) {
        authNoticePhone.textContent = 'Vui lòng nhập số điện thoại của đồng chí!';
        inputAuthPhone.focus();
        return;
      }
      try {
        btnSendOtp.disabled = true;
        btnSendOtp.textContent = '⏳ Đang gửi mã qua Zalo...';
        authNoticePhone.textContent = '';
        await triggerSendOtp(phone);
      } catch (err) {
        authNoticePhone.textContent = '⚠️ ' + err.message;
      } finally {
        btnSendOtp.disabled = false;
        btnSendOtp.textContent = '⚡ Lấy mã xác thực OTP';
      }
    });

    inputAuthPhone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') btnSendOtp.click();
    });
  }

  if (btnResendOtp) {
    btnResendOtp.addEventListener('click', async () => {
      if (!currentAuthTargetPhone || btnResendOtp.disabled) return;
      try {
        authNoticeOtp.textContent = '⏳ Đang gửi lại mã qua Zalo...';
        authNoticeOtp.style.color = '#0068ff';
        await triggerSendOtp(currentAuthTargetPhone);
        authNoticeOtp.textContent = '✓ Đã gửi lại mã OTP mới qua Zalo của đồng chí!';
        authNoticeOtp.style.color = '#059669';
        setTimeout(() => {
          authNoticeOtp.textContent = '';
          authNoticeOtp.style.color = 'var(--primary-red)';
        }, 5000);
      } catch (err) {
        authNoticeOtp.textContent = '⚠️ ' + err.message;
        authNoticeOtp.style.color = 'var(--primary-red)';
      }
    });
  }

  if (btnBackToStep1) {
    btnBackToStep1.addEventListener('click', () => {
      authStep2.style.display = 'none';
      authStep1.style.display = 'block';
      if (inputAuthPhone) inputAuthPhone.focus();
    });
  }

  if (btnVerifyOtp && inputAuthOtp) {
    btnVerifyOtp.addEventListener('click', async () => {
      const otp = inputAuthOtp.value.trim();
      if (!otp || otp.length < 6) {
        authNoticeOtp.textContent = 'Vui lòng nhập đủ 6 chữ số mã OTP!';
        inputAuthOtp.focus();
        return;
      }

      try {
        btnVerifyOtp.disabled = true;
        btnVerifyOtp.textContent = '⏳ Đang xác nhận...';
        authNoticeOtp.textContent = '';

        const res = await fetch('/api/auth/verify-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone: currentAuthTargetPhone,
            otp: otp,
            session_id: sessionId
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Xác thực OTP thất bại');
        }

        applyCadreLogin(data.can_bo, data.token);
        if (modalAuth) modalAuth.style.display = 'none';
        showToast(`✓ Đăng nhập thành công! Xin chào đồng chí ${data.can_bo.ho_ten} (${data.can_bo.chuc_vu}).`, 'success');
        loadSidebarSessions();
      } catch (err) {
        authNoticeOtp.textContent = '❌ ' + err.message;
      } finally {
        btnVerifyOtp.disabled = false;
        btnVerifyOtp.textContent = '✓ Xác nhận Đăng nhập';
      }
    });

    inputAuthOtp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') btnVerifyOtp.click();
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      if (confirm('Đồng chí có chắc chắn muốn đăng xuất? (Hệ thống sẽ chuyển về Chế độ Khách)')) {
        try {
          const token = localStorage.getItem('cva_auth_token') || '';
          await fetch('/api/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token, session_id: sessionId })
          });
        } catch {}

        applyGuestMode();
        if (modalAuth) modalAuth.style.display = 'none';
      }
    });
  }

  if (btnGoToAdminFromModal) {
    btnGoToAdminFromModal.addEventListener('click', () => {
      if (modalAuth) modalAuth.style.display = 'none';
      showView('admin');
    });
  }

  // ============================================================================
  // 8. QUẢN LÝ DANH BẠ CÁN BỘ (CRUD DÀNH CHO ADMIN) & GỬI TIN NHẮN BOT ZALO
  // ============================================================================
  const cadresTableBody = document.getElementById('cadresTableBody');
  const inputSearchCadre = document.getElementById('inputSearchCadre');
  const btnOpenAddCadreModal = document.getElementById('btnOpenAddCadreModal');
  const modalCadreCrud = document.getElementById('modalCadreCrud');
  const btnCloseCadreModal = document.getElementById('btnCloseCadreModal');
  const btnCancelCadreModal = document.getElementById('btnCancelCadreModal');
  const formCadreCrud = document.getElementById('formCadreCrud');
  const cadreCrudModalTitle = document.getElementById('cadreCrudModalTitle');
  const crudCadreId = document.getElementById('crudCadreId');
  const crudHoTen = document.getElementById('crudHoTen');
  const crudSoDienThoai = document.getElementById('crudSoDienThoai');
  const crudChucVu = document.getElementById('crudChucVu');
  const crudCoQuan = document.getElementById('crudCoQuan');
  const crudVaiTro = document.getElementById('crudVaiTro');
  const crudCadreNotice = document.getElementById('crudCadreNotice');

  // Các phần tử phục vụ chức năng Gửi Tin Nhắn Bot Zalo
  const chkSelectAllCadres = document.getElementById('chkSelectAllCadres');
  const btnOpenSendZaloModal = document.getElementById('btnOpenSendZaloModal');
  const btnSendZaloText = document.getElementById('btnSendZaloText');
  const modalSendZalo = document.getElementById('modalSendZalo');
  const btnCloseSendZaloModal = document.getElementById('btnCloseSendZaloModal');
  const btnCancelSendZaloModal = document.getElementById('btnCancelSendZaloModal');
  const zaloRecipientCount = document.getElementById('zaloRecipientCount');
  const zaloRecipientsContainer = document.getElementById('zaloRecipientsContainer');
  const btnSelectAllLinkedZalo = document.getElementById('btnSelectAllLinkedZalo');
  const btnClearSelectedZalo = document.getElementById('btnClearSelectedZalo');
  const zaloMsgTitle = document.getElementById('zaloMsgTitle');
  const zaloMsgContent = document.getElementById('zaloMsgContent');
  const zaloCharCount = document.getElementById('zaloCharCount');
  const zaloPreviewTitle = document.getElementById('zaloPreviewTitle');
  const zaloPreviewRecipient = document.getElementById('zaloPreviewRecipient');
  const zaloPreviewContent = document.getElementById('zaloPreviewContent');
  const zaloSendStatusArea = document.getElementById('zaloSendStatusArea');
  const btnSubmitSendZalo = document.getElementById('btnSubmitSendZalo');

  let adminCadresList = [];
  const selectedCadreIds = new Set();

  function updateSelectedCadresUI() {
    const total = selectedCadreIds.size;
    if (btnSendZaloText) {
      btnSendZaloText.textContent = total > 0 ? `Gửi Tin Nhắn Zalo (${total})` : 'Gửi Tin Nhắn Zalo';
    }

    if (chkSelectAllCadres) {
      const visibleCheckboxes = cadresTableBody ? cadresTableBody.querySelectorAll('.chk-select-cadre') : [];
      if (visibleCheckboxes.length === 0) {
        chkSelectAllCadres.checked = false;
        chkSelectAllCadres.indeterminate = false;
      } else {
        let checkedCount = 0;
        visibleCheckboxes.forEach(chk => {
          if (chk.checked) checkedCount++;
        });
        chkSelectAllCadres.checked = checkedCount === visibleCheckboxes.length;
        chkSelectAllCadres.indeterminate = checkedCount > 0 && checkedCount < visibleCheckboxes.length;
      }
    }
  }

  async function loadAdminCadres() {
    if (!cadresTableBody) return;
    cadresTableBody.innerHTML = '<tr><td colspan="9" class="loading-td">Đang tải danh bạ cán bộ...</td></tr>';

    try {
      const res = await fetch('/api/admin/cadres');
      if (!res.ok) throw new Error('Không thể tải danh bạ');
      const data = await res.json();
      adminCadresList = data.cadres || [];
      renderAdminCadresTable(adminCadresList);
      if (statAdminCadres) statAdminCadres.textContent = adminCadresList.length;
    } catch (err) {
      cadresTableBody.innerHTML = `<tr><td colspan="9" style="color:#ef4444; padding:20px;">Lỗi tải dữ liệu: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function renderAdminCadresTable(list) {
    if (!cadresTableBody) return;
    const filter = (inputSearchCadre ? inputSearchCadre.value.trim().toLowerCase() : '');
    const filtered = list.filter(c => 
      !filter || 
      (c.ho_ten && c.ho_ten.toLowerCase().includes(filter)) || 
      (c.so_dien_thoai && c.so_dien_thoai.includes(filter)) ||
      (c.co_quan && c.co_quan.toLowerCase().includes(filter))
    );

    if (filtered.length === 0) {
      cadresTableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:30px;">Danh bạ chưa có cán bộ nào phù hợp. Bấm "➕ Thêm Cán Bộ Mới" để thêm.</td></tr>';
      updateSelectedCadresUI();
      return;
    }

    cadresTableBody.innerHTML = filtered.map((c, idx) => {
      const isAdmin = c.vai_tro === 'admin';
      const roleBadge = isAdmin 
        ? '<span class="badge-role-admin">👑 Admin</span>' 
        : '<span class="badge-role-cadre">Cán bộ</span>';

      const isMainAdmin = c.so_dien_thoai === '0327777707';
      const isLinkedZalo = Boolean(c.zalo_chat_id || c.zalo_user_id);
      const isChecked = selectedCadreIds.has(c.can_bo_id);

      const zaloBadge = isLinkedZalo
        ? `<span class="badge-zalo-linked" title="Đã kích hoạt Zalo Bot (Chat ID: ${escapeHtml(c.zalo_chat_id || c.zalo_user_id || '')})">● Đã liên kết Zalo</span>`
        : `<span class="badge-zalo-unlinked" title="Chưa kích hoạt nhận tin qua Bot Zalo">○ Chưa liên kết Zalo</span>`;

      return `
        <tr class="${isChecked ? 'row-selected' : ''}">
          <td style="text-align: center;">
            <input type="checkbox" class="chk-select-cadre" data-id="${c.can_bo_id}" ${isChecked ? 'checked' : ''}>
          </td>
          <td style="color:#94a3b8; font-size:12px;">${idx + 1}</td>
          <td><b>${escapeHtml(c.ho_ten || '')}</b></td>
          <td><code style="color:#38bdf8; font-weight:600;">${escapeHtml(c.so_dien_thoai || 'Chưa có')}</code></td>
          <td>${escapeHtml(c.chuc_vu || '')}</td>
          <td>${escapeHtml(c.co_quan || '')}</td>
          <td>${zaloBadge}</td>
          <td>${roleBadge}</td>
          <td style="text-align: center;">
            <button class="btn-table-action btn-zalo-row" data-id="${c.can_bo_id}" title="Gửi tin nhắn Zalo riêng cho cán bộ này">💬 Gửi Zalo</button>
            <button class="btn-table-action btn-edit-cadre" data-id="${c.can_bo_id}">✏️ Sửa</button>
            ${!isMainAdmin ? `<button class="btn-table-action delete btn-delete-cadre" data-id="${c.can_bo_id}" data-name="${escapeHtml(c.ho_ten)}">🗑️ Xoá</button>` : ''}
          </td>
        </tr>
      `;
    }).join('');

    // Gắn sự kiện chọn từng dòng checkbox
    cadresTableBody.querySelectorAll('.chk-select-cadre').forEach(chk => {
      chk.addEventListener('change', () => {
        const cid = chk.getAttribute('data-id');
        if (chk.checked) {
          selectedCadreIds.add(cid);
        } else {
          selectedCadreIds.delete(cid);
        }
        updateSelectedCadresUI();
      });
    });

    // Gắn sự kiện nút Gửi Zalo từng người
    cadresTableBody.querySelectorAll('.btn-zalo-row').forEach(btn => {
      btn.addEventListener('click', () => {
        const cid = btn.getAttribute('data-id');
        selectedCadreIds.clear();
        selectedCadreIds.add(cid);
        updateSelectedCadresUI();
        openSendZaloModal();
      });
    });

    // Gắn sự kiện nút Sửa
    cadresTableBody.querySelectorAll('.btn-edit-cadre').forEach(btn => {
      btn.addEventListener('click', () => {
        const cid = btn.getAttribute('data-id');
        const target = adminCadresList.find(x => x.can_bo_id === cid);
        if (target) openCadreModal(target);
      });
    });

    // Gắn sự kiện nút Xoá
    cadresTableBody.querySelectorAll('.btn-delete-cadre').forEach(btn => {
      btn.addEventListener('click', async () => {
        const cid = btn.getAttribute('data-id');
        const name = btn.getAttribute('data-name');
        if (confirm(`Đồng chí có chắc chắn muốn xoá cán bộ "${name}" khỏi danh bạ hệ thống?`)) {
          try {
            const res = await fetch(`/api/admin/cadres/${cid}`, { method: 'DELETE' });
            const d = await res.json();
            if (!res.ok) throw new Error(d.detail || 'Lỗi khi xoá cán bộ');
            selectedCadreIds.delete(cid);
            showToast(`✓ Đã xoá cán bộ "${name}" khỏi danh bạ thành công!`, 'success');
            await loadAdminCadres();
          } catch (err) {
            showToast('Lỗi xoá cán bộ: ' + err.message, 'error');
          }
        }
      });
    });

    updateSelectedCadresUI();
  }

  // Sự kiện chọn tất cả checkbox ở Header
  if (chkSelectAllCadres) {
    chkSelectAllCadres.addEventListener('change', () => {
      const isChecked = chkSelectAllCadres.checked;
      const visibleCheckboxes = cadresTableBody ? cadresTableBody.querySelectorAll('.chk-select-cadre') : [];
      visibleCheckboxes.forEach(chk => {
        const cid = chk.getAttribute('data-id');
        chk.checked = isChecked;
        if (isChecked) {
          selectedCadreIds.add(cid);
        } else {
          selectedCadreIds.delete(cid);
        }
      });
      updateSelectedCadresUI();
    });
  }

  if (inputSearchCadre) {
    inputSearchCadre.addEventListener('input', () => renderAdminCadresTable(adminCadresList));
  }

  function openCadreModal(target = null) {
    if (!modalCadreCrud) return;
    if (crudCadreNotice) crudCadreNotice.textContent = '';

    if (target) {
      if (cadreCrudModalTitle) cadreCrudModalTitle.textContent = '✏️ Chỉnh Sửa Thông Tin Cán Bộ';
      if (crudCadreId) crudCadreId.value = target.can_bo_id || '';
      if (crudHoTen) crudHoTen.value = target.ho_ten || '';
      if (crudSoDienThoai) crudSoDienThoai.value = target.so_dien_thoai || '';
      if (crudChucVu) crudChucVu.value = target.chuc_vu || '';
      if (crudCoQuan) crudCoQuan.value = target.co_quan || '';
      if (crudVaiTro) crudVaiTro.value = target.vai_tro || 'can_bo';
    } else {
      if (cadreCrudModalTitle) cadreCrudModalTitle.textContent = '➕ Thêm Cán Bộ Mới';
      if (crudCadreId) crudCadreId.value = '';
      if (crudHoTen) crudHoTen.value = '';
      if (crudSoDienThoai) crudSoDienThoai.value = '';
      if (crudChucVu) crudChucVu.value = 'Chuyên viên';
      if (crudCoQuan) crudCoQuan.value = 'Văn phòng Đảng uỷ';
      if (crudVaiTro) crudVaiTro.value = 'can_bo';
    }

    modalCadreCrud.style.display = 'grid';
    if (crudHoTen) crudHoTen.focus();
  }

  if (btnOpenAddCadreModal) btnOpenAddCadreModal.addEventListener('click', () => openCadreModal());
  if (btnCloseCadreModal) btnCloseCadreModal.addEventListener('click', () => modalCadreCrud.style.display = 'none');
  if (btnCancelCadreModal) btnCancelCadreModal.addEventListener('click', () => modalCadreCrud.style.display = 'none');

  if (formCadreCrud) {
    formCadreCrud.addEventListener('submit', async (e) => {
      e.preventDefault();
      const cid = crudCadreId.value.trim();
      const payload = {
        ho_ten: crudHoTen.value.trim(),
        so_dien_thoai: crudSoDienThoai.value.trim(),
        chuc_vu: crudChucVu.value.trim(),
        co_quan: crudCoQuan.value.trim(),
        vai_tro: crudVaiTro.value
      };

      try {
        const isEdit = Boolean(cid);
        const url = isEdit ? `/api/admin/cadres/${cid}` : '/api/admin/cadres';
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
          method: method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const d = await res.json();
        if (!res.ok) throw new Error(d.detail || 'Lưu cán bộ thất bại');

        modalCadreCrud.style.display = 'none';
        await loadAdminCadres();
      } catch (err) {
        if (crudCadreNotice) crudCadreNotice.textContent = '⚠️ ' + err.message;
      }
    });
  }

  // ============================================================================
  // LOGIC MODAL SOẠN & GỬI TIN NHẮN BOT ZALO CHO CÁN BỘ
  // ============================================================================
  function updateZaloPreview() {
    const titleVal = zaloMsgTitle ? (zaloMsgTitle.value.trim() || 'Thông báo từ Văn phòng Đảng uỷ') : '';
    const contentVal = zaloMsgContent ? zaloMsgContent.value.trim() : '';

    if (zaloPreviewTitle) {
      zaloPreviewTitle.innerHTML = `🔔 <b>${escapeHtml(titleVal.toUpperCase())}</b>`;
    }

    if (zaloPreviewRecipient) {
      const selectedCadres = adminCadresList.filter(c => selectedCadreIds.has(c.can_bo_id));
      if (selectedCadres.length === 1) {
        const c = selectedCadres[0];
        const extra = [c.chuc_vu, c.co_quan].filter(Boolean).join(' - ');
        zaloPreviewRecipient.innerHTML = `Kính gửi đồng chí: <b>${escapeHtml(c.ho_ten)}</b> ${extra ? `<i>(${escapeHtml(extra)})</i>` : ''}`;
      } else if (selectedCadres.length > 1) {
        zaloPreviewRecipient.innerHTML = `Kính gửi: <b>Các đồng chí được triệu tập / phân công</b> <i>(${selectedCadres.length} đồng chí)</i>`;
      } else {
        zaloPreviewRecipient.innerHTML = `Kính gửi đồng chí: <i>[Chưa chọn cán bộ nhận]</i>`;
      }
    }

    if (zaloPreviewContent) {
      zaloPreviewContent.textContent = contentVal || '(Chưa có nội dung tin nhắn)';
    }

    if (zaloCharCount && zaloMsgContent) {
      const len = zaloMsgContent.value.length;
      zaloCharCount.textContent = `${len} / 1900 ký tự`;
      zaloCharCount.style.color = len > 1800 ? '#ef4444' : '#94a3b8';
    }
  }

  function renderZaloRecipientsBox() {
    if (!zaloRecipientsContainer) return;

    if (adminCadresList.length === 0) {
      zaloRecipientsContainer.innerHTML = '<div style="color:#94a3b8; font-size:12.5px; padding:10px;">Chưa có dữ liệu cán bộ.</div>';
      return;
    }

    zaloRecipientsContainer.innerHTML = adminCadresList.map(c => {
      const isSelected = selectedCadreIds.has(c.can_bo_id);
      const isLinkedZalo = Boolean(c.zalo_chat_id || c.zalo_user_id);
      const detailInfo = [c.chuc_vu, c.co_quan].filter(Boolean).join(' - ');

      const badgeHtml = isLinkedZalo
        ? '<span class="badge-zalo-linked" style="font-size:10.5px;">● Đã liên kết Zalo</span>'
        : '<span class="badge-zalo-unlinked" style="font-size:10.5px;">○ Chưa liên kết Zalo</span>';

      return `
        <div class="zalo-recipient-item ${isSelected ? 'selected' : ''} ${!isLinkedZalo ? 'unlinked' : ''}" data-id="${c.can_bo_id}">
          <div style="display: flex; align-items: center; gap: 8px;">
            <input type="checkbox" class="modal-chk-recipient" data-id="${c.can_bo_id}" ${isSelected ? 'checked' : ''}>
            <div>
              <div style="font-weight: 700; color: #1e293b;">${escapeHtml(c.ho_ten || '')}</div>
              <div style="font-size: 11.5px; color: #64748b;">${escapeHtml(detailInfo || 'Cán bộ')} - SĐT: ${escapeHtml(c.so_dien_thoai || 'Chưa có')}</div>
            </div>
          </div>
          <div>${badgeHtml}</div>
        </div>
      `;
    }).join('');

    // Gắn sự kiện click chọn người nhận trong modal
    zaloRecipientsContainer.querySelectorAll('.zalo-recipient-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.tagName.toLowerCase() === 'input') return;
        const cid = item.getAttribute('data-id');
        const chk = item.querySelector('.modal-chk-recipient');
        if (selectedCadreIds.has(cid)) {
          selectedCadreIds.delete(cid);
          if (chk) chk.checked = false;
          item.classList.remove('selected');
        } else {
          selectedCadreIds.add(cid);
          if (chk) chk.checked = true;
          item.classList.add('selected');
        }
        if (zaloRecipientCount) zaloRecipientCount.textContent = selectedCadreIds.size;
        updateSelectedCadresUI();
        updateZaloPreview();
      });
    });

    zaloRecipientsContainer.querySelectorAll('.modal-chk-recipient').forEach(chk => {
      chk.addEventListener('change', () => {
        const cid = chk.getAttribute('data-id');
        const item = chk.closest('.zalo-recipient-item');
        if (chk.checked) {
          selectedCadreIds.add(cid);
          if (item) item.classList.add('selected');
        } else {
          selectedCadreIds.delete(cid);
          if (item) item.classList.remove('selected');
        }
        if (zaloRecipientCount) zaloRecipientCount.textContent = selectedCadreIds.size;
        updateSelectedCadresUI();
        updateZaloPreview();
      });
    });

    if (zaloRecipientCount) zaloRecipientCount.textContent = selectedCadreIds.size;
  }

  function openSendZaloModal() {
    if (!modalSendZalo) return;

    // Nếu chưa chọn ai, tự động chọn các cán bộ đã liên kết Zalo để tiện nhất
    if (selectedCadreIds.size === 0 && adminCadresList.length > 0) {
      adminCadresList.forEach(c => {
        if (c.zalo_chat_id || c.zalo_user_id) {
          selectedCadreIds.add(c.can_bo_id);
        }
      });
      updateSelectedCadresUI();
    }

    if (zaloSendStatusArea) {
      zaloSendStatusArea.style.display = 'none';
      zaloSendStatusArea.innerHTML = '';
    }

    renderZaloRecipientsBox();
    updateZaloPreview();

    modalSendZalo.style.display = 'grid';
    if (zaloMsgContent) zaloMsgContent.focus();
  }

  if (btnOpenSendZaloModal) {
    btnOpenSendZaloModal.addEventListener('click', () => openSendZaloModal());
  }

  if (btnCloseSendZaloModal) {
    btnCloseSendZaloModal.addEventListener('click', () => modalSendZalo.style.display = 'none');
  }

  if (btnCancelSendZaloModal) {
    btnCancelSendZaloModal.addEventListener('click', () => modalSendZalo.style.display = 'none');
  }

  // Chọn tất cả đã liên kết Zalo
  if (btnSelectAllLinkedZalo) {
    btnSelectAllLinkedZalo.addEventListener('click', () => {
      selectedCadreIds.clear();
      adminCadresList.forEach(c => {
        if (c.zalo_chat_id || c.zalo_user_id) {
          selectedCadreIds.add(c.can_bo_id);
        }
      });
      renderZaloRecipientsBox();
      updateSelectedCadresUI();
      updateZaloPreview();
    });
  }

  // Bỏ chọn tất cả
  if (btnClearSelectedZalo) {
    btnClearSelectedZalo.addEventListener('click', () => {
      selectedCadreIds.clear();
      renderZaloRecipientsBox();
      updateSelectedCadresUI();
      updateZaloPreview();
    });
  }

  // Gợi ý mẫu tin nhắn nhanh
  document.querySelectorAll('.btn-template-tag').forEach(btn => {
    btn.addEventListener('click', () => {
      const tpl = btn.getAttribute('data-tpl');
      if (tpl === 'hop') {
        if (zaloMsgTitle) zaloMsgTitle.value = 'Mời tham dự cuộc họp Thường trực Đảng uỷ';
        if (zaloMsgContent) {
          zaloMsgContent.value = `Thực hiện ý kiến chỉ đạo của Thường trực Đảng uỷ xã Công Hải, Văn phòng Đảng uỷ trân trọng kính mời đồng chí tham dự cuộc họp:\n- Thời gian: 08 giờ 00, ngày .../.../2026.\n- Địa điểm: Phòng họp Văn phòng Đảng uỷ xã Công Hải.\n- Nội dung: Cho ý kiến chỉ đạo về các nhiệm vụ trọng tâm chuẩn bị tổng kết năm.\nĐề nghị đồng chí sắp xếp công việc và có mặt đúng giờ./.`;
        }
      } else if (tpl === 'dondoc') {
        if (zaloMsgTitle) zaloMsgTitle.value = 'Đôn đốc tiến độ nộp Báo cáo tổng kết năm 2026';
        if (zaloMsgContent) {
          zaloMsgContent.value = `Kính gửi đồng chí, để chuẩn bị chu đáo hồ sơ trình Ban Thường vụ Đảng uỷ tổng kết năm 2026, Văn phòng Đảng uỷ đề nghị đồng chí khẩn trương hoàn thiện Báo cáo của cơ quan/đơn vị và gửi về Văn phòng trước ngày 25/11/2026.\nTrân trọng cảm ơn sự phối hợp của đồng chí./.`;
        }
      } else if (tpl === 'thongbao') {
        if (zaloMsgTitle) zaloMsgTitle.value = 'Thông báo chỉ đạo của Thường trực Đảng uỷ';
        if (zaloMsgContent) {
          zaloMsgContent.value = `Văn phòng Đảng uỷ xã Công Hải trân trọng thông báo ý kiến chỉ đạo của Thường trực Đảng uỷ về việc triển khai nhiệm vụ đột xuất...\nĐề nghị đồng chí nắm bắt và chủ động triển khai thực hiện./.`;
        }
      }
      updateZaloPreview();
    });
  });

  if (zaloMsgTitle) zaloMsgTitle.addEventListener('input', updateZaloPreview);
  if (zaloMsgContent) zaloMsgContent.addEventListener('input', updateZaloPreview);

  // Gửi tin nhắn Zalo
  if (btnSubmitSendZalo) {
    btnSubmitSendZalo.addEventListener('click', async () => {
      if (selectedCadreIds.size === 0) {
        showToast('⚠️ Vui lòng chọn ít nhất một cán bộ để gửi tin nhắn.', 'warning');
        return;
      }

      const content = zaloMsgContent ? zaloMsgContent.value.trim() : '';
      if (!content) {
        showToast('⚠️ Vui lòng nhập nội dung tin nhắn cần gửi.', 'warning');
        if (zaloMsgContent) zaloMsgContent.focus();
        return;
      }

      const title = zaloMsgTitle ? (zaloMsgTitle.value.trim() || 'Thông báo từ Văn phòng Đảng uỷ') : 'Thông báo từ Văn phòng Đảng uỷ';
      const targetCadreIds = Array.from(selectedCadreIds);

      btnSubmitSendZalo.disabled = true;
      btnSubmitSendZalo.innerHTML = '<span>⏳ Đang gửi tin qua Bot Zalo...</span>';

      if (zaloSendStatusArea) {
        zaloSendStatusArea.style.display = 'block';
        zaloSendStatusArea.className = 'zalo-status-banner warning';
        zaloSendStatusArea.innerHTML = `Đang kết nối Zalo Bot Platform gửi tin nhắn tới ${targetCadreIds.length} cán bộ, vui lòng đợi...`;
      }

      try {
        const res = await fetch('/api/admin/cadres/send-zalo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            can_bo_ids: targetCadreIds,
            tieu_de: title,
            noi_dung: content
          })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Lỗi khi gửi tin qua Bot Zalo');

        const { total_selected, total_sent, total_failed, details } = data;

        let statusClass = 'success';
        if (total_sent === 0 && total_failed > 0) statusClass = 'error';
        else if (total_failed > 0) statusClass = 'warning';

        let html = `<b>Kết quả gửi tin nhắn Bot Zalo:</b><br>`;
        html += `• Đã chọn: <b>${total_selected}</b> cán bộ<br>`;
        html += `• Gửi thành công: <b style="color:#16a34a;">${total_sent}</b> cán bộ<br>`;
        if (total_failed > 0) {
          html += `• Thất bại / Chưa nhận: <b style="color:#ef4444;">${total_failed}</b> cán bộ<br>`;
          html += `<div style="margin-top:6px; font-size:12px; max-height:80px; overflow-y:auto; border-top:1px dashed #cbd5e1; padding-top:4px;">`;
          details.filter(d => d.status === 'failed').forEach(d => {
            html += `• <b>${escapeHtml(d.ho_ten)}</b>: ${escapeHtml(d.reason || 'Lỗi gửi')}<br>`;
          });
          html += `</div>`;
        }

        if (zaloSendStatusArea) {
          zaloSendStatusArea.className = `zalo-status-banner ${statusClass}`;
          zaloSendStatusArea.innerHTML = html;
        }

        if (total_sent > 0 && total_failed === 0) {
          setTimeout(() => {
            if (modalSendZalo) modalSendZalo.style.display = 'none';
          }, 2500);
        }
      } catch (err) {
        if (zaloSendStatusArea) {
          zaloSendStatusArea.className = 'zalo-status-banner error';
          zaloSendStatusArea.innerHTML = `❌ Lỗi: ${escapeHtml(err.message)}`;
        }
      } finally {
        btnSubmitSendZalo.disabled = false;
        btnSubmitSendZalo.innerHTML = '<span>🚀 Gửi Tin Nhắn Zalo</span>';
      }
    });
  }

  // ============================================================================
  // 9. QUẢN LÝ MÔ HÌNH AI TRONG ADMIN (GEMINI / DEEPSEEK / OLLAMA)
  // ============================================================================
  const cardModelGemini = document.getElementById('cardModelGemini');
  const cardModelDeepseek = document.getElementById('cardModelDeepseek');
  const cardModelOllama = document.getElementById('cardModelOllama');

  function updateModelCardsUI(currentModel, provider) {
    if (cardModelGemini) cardModelGemini.classList.remove('active');
    if (cardModelDeepseek) cardModelDeepseek.classList.remove('active');
    if (cardModelOllama) cardModelOllama.classList.remove('active');

    const m = (currentModel || '').toLowerCase();
    const p = (provider || '').toLowerCase();

    if (p === 'gemini' || m.includes('gemini')) {
      if (cardModelGemini) cardModelGemini.classList.add('active');
    } else if (p === 'local' || m.includes('qwen') || m.includes('r1')) {
      if (cardModelOllama) cardModelOllama.classList.add('active');
    } else {
      if (cardModelDeepseek) cardModelDeepseek.classList.add('active');
    }
  }

  if (cardModelGemini) {
    cardModelGemini.addEventListener('click', async () => {
      await switchActiveModel('gemini-3.5-flash-lite', 'gemini');
      updateModelCardsUI('gemini-3.5-flash-lite', 'gemini');
      if (topbarModelName) topbarModelName.textContent = 'Gemini 3.5 Flash Lite';
      showToast('✓ Đã kích hoạt Google Gemini 3.5 Flash Lite làm Động cơ chính!', 'success');
    });
  }

  if (cardModelDeepseek) {
    cardModelDeepseek.addEventListener('click', async () => {
      await switchActiveModel('deepseek-chat', 'cloud');
      updateModelCardsUI('deepseek-chat', 'cloud');
      if (topbarModelName) topbarModelName.textContent = 'DeepSeek Cloud (671B)';
      showToast('✓ Đã kích hoạt DeepSeek Cloud (671B) làm Động cơ chính!', 'success');
    });
  }

  if (cardModelOllama) {
    cardModelOllama.addEventListener('click', async () => {
      await switchActiveModel('qwen2.5:3b', 'local');
      updateModelCardsUI('qwen2.5:3b', 'local');
      if (topbarModelName) topbarModelName.textContent = 'Ollama Local (3B)';
      showToast('✓ Đã kích hoạt Ollama Local làm Động cơ chính!', 'success');
    });
  }

  // --- ADMIN DASHBOARD DATA LOADERS ---
  const statAdminMessages = document.getElementById('statAdminMessages');
  const statAdminCadres = document.getElementById('statAdminCadres');
  const statAdminDisk = document.getElementById('statAdminDisk');
  const statAdminAiModel = document.getElementById('statAdminAiModel');
  const chatLogsTableBody = document.getElementById('chatLogsTableBody');
  const inputSearchChatLogs = document.getElementById('inputSearchChatLogs');
  const btnSearchChatLogs = document.getElementById('btnSearchChatLogs');
  const serverLogsPre = document.getElementById('serverLogsPre');
  const btnRefreshServerLogs = document.getElementById('btnRefreshServerLogs');

  async function loadAdminDashboard() {
    await Promise.all([
      loadAdminCadres(),
      loadAdminMetrics(),
      loadAdminChatLogs(),
      loadAdminServerLogs()
    ]);
  }

  async function loadAdminMetrics() {
    try {
      const res = await fetch('/api/admin/system/metrics');
      if (!res.ok) return;
      const d = await res.json();

      if (statAdminMessages) statAdminMessages.textContent = d.database?.messages || 0;
      if (statAdminCadres) statAdminCadres.textContent = d.database?.cadres || 0;
      if (statAdminDisk && d.disk) {
        statAdminDisk.textContent = `${d.disk.used_gb} / ${d.disk.total_gb} GB (${d.disk.percent}%)`;
      }
      if (statAdminAiModel && d.ai) {
        statAdminAiModel.textContent = `${d.ai.current_model} [${d.ai.provider?.toUpperCase()}]`;
        updateModelCardsUI(d.ai.current_model, d.ai.provider);
      }
    } catch (err) {
      console.warn('Lỗi tải metrics admin:', err);
    }
  }

  const filterSessionChannel = document.getElementById('filterSessionChannel');
  const btnRefreshSessions = document.getElementById('btnRefreshSessions');
  const modalSessionDetail = document.getElementById('modalSessionDetail');
  const btnCloseSessionModal = document.getElementById('btnCloseSessionModal');
  const btnCancelSessionModal = document.getElementById('btnCancelSessionModal');
  const drawerChannelIcon = document.getElementById('drawerChannelIcon');
  const drawerCadreName = document.getElementById('drawerCadreName');
  const drawerSessionBadge = document.getElementById('drawerSessionBadge');
  const drawerSessionMeta = document.getElementById('drawerSessionMeta');
  const sessionChatBody = document.getElementById('sessionChatBody');
  const drawerMessageCount = document.getElementById('drawerMessageCount');

  async function loadAdminChatLogs() {
    if (!chatLogsTableBody) return;
    chatLogsTableBody.innerHTML = '<tr><td colspan="7" class="loading-td">Đang tải danh sách phiên làm việc...</td></tr>';

    try {
      const kw = inputSearchChatLogs ? inputSearchChatLogs.value.trim() : '';
      const channel = filterSessionChannel ? filterSessionChannel.value : '';
      const url = `/api/admin/sessions?search=${encodeURIComponent(kw)}&channel=${encodeURIComponent(channel)}&page=1&page_size=50`;

      const res = await fetch(url);
      if (!res.ok) throw new Error('Không thể tải danh sách phiên');
      const data = await res.json();
      const sessions = data.sessions || [];

      if (sessions.length === 0) {
        chatLogsTableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#94a3b8; padding:35px;">Chưa có phiên làm việc nào phù hợp.</td></tr>';
        return;
      }

      chatLogsTableBody.innerHTML = sessions.map(s => {
        const isZalo = s.channel === 'zalo' || (s.session_id && String(s.session_id).startsWith('zalo_'));
        const channelBadge = isZalo
          ? '<span style="display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:700; background:#0068ff; color:white; padding:2px 8px; border-radius:4px;">💬 Zalo Bot</span>'
          : '<span style="display:inline-flex; align-items:center; gap:4px; font-size:11px; font-weight:700; background:#475569; color:white; padding:2px 8px; border-radius:4px;">🌐 Cổng Web</span>';

        const cadreInfo = `
          <div style="font-weight:700; color:var(--text-main);">${escapeHtml(s.ho_ten || 'Cán bộ')}</div>
          ${s.so_dien_thoai ? `<div style="font-size:11.5px; color:#64748b;">📞 ${escapeHtml(s.so_dien_thoai)}</div>` : ''}
          ${s.co_quan ? `<div style="font-size:11px; color:#94a3b8;">🏢 ${escapeHtml(s.co_quan)}</div>` : ''}
        `;

        const summaryPreview = `
          <div style="font-size:12.5px; color:#334155; line-height:1.4;">
            <span style="color:#0284c7; font-weight:600;">Hỏi:</span> "${escapeHtml((s.last_user_message || s.first_user_message || '').substring(0, 100))}"
          </div>
          <div style="font-size:11.5px; color:#64748b; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:400px;">
            <span style="color:#10b981; font-weight:600;">Đáp:</span> ${escapeHtml((s.last_bot_reply || '').substring(0, 120))}...
          </div>
        `;

        const msgCountBadge = `
          <div style="text-align:center;">
            <span style="font-size:13px; font-weight:700; color:#0284c7; background:#e0f2fe; padding:2px 10px; border-radius:10px;">${s.total_messages || 1}</span>
          </div>
        `;

        const timeDisplay = `
          <div style="font-size:12px; font-weight:600; color:#334155;">${escapeHtml((s.last_activity || '').substring(11, 16))}</div>
          <div style="font-size:11px; color:#94a3b8;">${escapeHtml((s.last_activity || '').substring(0, 10))}</div>
        `;

        const actionBtn = `
          <div style="text-align:center;">
            <button class="btn-chs-primary" style="padding:5px 12px; font-size:12px;" onclick="window.viewSessionDetail('${escapeHtml(s.session_id)}')">
              👁️ Mở xem
            </button>
          </div>
        `;

        return `
          <tr style="cursor:pointer;" onclick="window.viewSessionDetail('${escapeHtml(s.session_id)}')">
            <td>${channelBadge}</td>
            <td>${cadreInfo}</td>
            <td>${summaryPreview}</td>
            <td>${msgCountBadge}</td>
            <td>${timeDisplay}</td>
            <td onclick="event.stopPropagation();">${actionBtn}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      chatLogsTableBody.innerHTML = `<tr><td colspan="6" style="color:#ef4444; padding:20px;">Lỗi tải dữ liệu: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  // Hàm mở xem toàn bộ mạch tin nhắn của một phiên (Session Detail View)
  window.viewSessionDetail = async function(sessionId) {
    if (!modalSessionDetail || !sessionChatBody) return;
    modalSessionDetail.style.display = 'flex';
    sessionChatBody.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:50px;">⏳ Đang tải toàn bộ hội thoại...</div>';

    try {
      const res = await fetch(`/api/admin/sessions/${encodeURIComponent(sessionId)}/messages`);
      if (!res.ok) throw new Error('Không thể tải tin nhắn phiên');
      const data = await res.json();
      const messages = data.messages || [];

      if (messages.length === 0) {
        sessionChatBody.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:40px;">Phiên này chưa có tin nhắn nào.</div>';
        return;
      }

      const first = messages[0];
      const isZalo = first.channel === 'zalo' || String(sessionId).startsWith('zalo_');
      if (drawerChannelIcon) drawerChannelIcon.textContent = isZalo ? '💬' : '🌐';
      if (drawerCadreName) drawerCadreName.textContent = `${first.ho_ten || 'Cán bộ'} ${first.so_dien_thoai ? `(${first.so_dien_thoai})` : ''}`;
      if (drawerSessionBadge) {
        drawerSessionBadge.textContent = isZalo ? 'Zalo Bot' : 'Cổng Web';
        drawerSessionBadge.style.background = isZalo ? '#0068ff' : '#475569';
      }
      if (drawerSessionMeta) {
        drawerSessionMeta.textContent = `Mã phiên: ${sessionId} • Bắt đầu: ${first.created_at || ''}`;
      }
      if (drawerMessageCount) {
        drawerMessageCount.textContent = `Tổng cộng: ${messages.length} lượt tin nhắn`;
      }

      sessionChatBody.innerHTML = messages.map(m => {
        return `
          <div style="display:flex; flex-direction:column; gap:10px;">
            <!-- Tin nhắn Người dùng -->
            <div style="align-self:flex-end; max-width:80%; background:#dc2626; color:white; padding:10px 14px; border-radius:14px 14px 2px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
              <div style="font-size:11px; opacity:0.85; margin-bottom:4px; display:flex; justify-content:space-between; gap:10px;">
                <span>👤 ${escapeHtml(m.ho_ten || 'Cán bộ')}</span>
                <span>${escapeHtml(m.created_at || '')}</span>
              </div>
              <div style="font-size:13.5px; line-height:1.45; white-space:pre-wrap;">${escapeHtml(m.message_text)}</div>
              ${m.attachment_names ? `<div style="margin-top:6px; font-size:11px; background:rgba(0,0,0,0.15); padding:3px 8px; border-radius:4px;">📎 Tệp: ${escapeHtml(m.attachment_names)}</div>` : ''}
            </div>

            <!-- Phản hồi Trợ lý AI -->
            <div style="align-self:flex-start; max-width:85%; background:white; border:1px solid #e2e8f0; color:#1e293b; padding:12px 16px; border-radius:14px 14px 14px 2px; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
              <div style="font-size:11px; color:#64748b; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; gap:10px; border-bottom:1px dashed #e2e8f0; padding-bottom:4px;">
                <span style="font-weight:700; color:var(--primary-red);">🤖 Trợ lý Chuyên viên ảo</span>
                <span style="font-size:10px; background:#f1f5f9; padding:1px 6px; border-radius:3px;">${escapeHtml(m.model_used || 'Gemini')} • ${m.latency_ms ? `${m.latency_ms}ms` : ''}</span>
              </div>
              <div style="font-size:13.5px; line-height:1.55; white-space:pre-wrap;">${escapeHtml(m.bot_reply)}</div>
            </div>
          </div>
        `;
      }).join('');

      // Tự động cuộn xuống tin nhắn cuối cùng
      sessionChatBody.scrollTop = sessionChatBody.scrollHeight;
    } catch (err) {
      sessionChatBody.innerHTML = `<div style="color:#ef4444; padding:20px; text-align:center;">Lỗi: ${escapeHtml(err.message)}</div>`;
    }
  };

  // Đóng Modal Session Detail
  function closeSessionModal() {
    if (modalSessionDetail) modalSessionDetail.style.display = 'none';
  }
  if (btnCloseSessionModal) btnCloseSessionModal.addEventListener('click', closeSessionModal);
  if (btnCancelSessionModal) btnCancelSessionModal.addEventListener('click', closeSessionModal);
  if (btnRefreshSessions) btnRefreshSessions.addEventListener('click', loadAdminChatLogs);
  if (filterSessionChannel) filterSessionChannel.addEventListener('change', loadAdminChatLogs);

  async function loadAdminServerLogs() {
    if (!serverLogsPre) return;
    serverLogsPre.textContent = '⏳ Đang đọc nhật ký máy chủ...';

    try {
      const res = await fetch('/api/admin/system/logs?limit=80');
      if (!res.ok) throw new Error('Không thể đọc tệp log');
      const d = await res.json();
      const lines = d.logs || [];
      serverLogsPre.textContent = lines.join('\n');
      const container = serverLogsPre.parentElement;
      if (container) container.scrollTop = container.scrollHeight;
    } catch (err) {
      serverLogsPre.textContent = `❌ Lỗi khi đọc log: ${err.message}`;
    }
  }

  if (btnRefreshServerLogs) btnRefreshServerLogs.addEventListener('click', loadAdminServerLogs);
  if (btnSearchChatLogs) btnSearchChatLogs.addEventListener('click', loadAdminChatLogs);
  if (inputSearchChatLogs) {
    inputSearchChatLogs.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') loadAdminChatLogs();
    });
  }

  // Khởi động
  checkAuthSession();
  checkStatus();
  loadModels();
  loadSidebarSessions();
  updateSendButton();
});

