/**
 * app.js — Giao diện Chat kiểu Gemini cho Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải
 */

document.addEventListener('DOMContentLoaded', () => {
  // Trạng thái phiên làm việc
  let sessionId = localStorage.getItem('cva_session_id') || '';
  let pendingAttachments = []; // [{ id, name, category_label, char_count }]
  let isSending = false;

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

  function renderModelSelector() {
    if (!modelList) return;
    modelList.innerHTML = '';

    const activeObj = availableModels.find(m => m.id === currentActiveModel);
    if (activeObj) {
      currentModelName.textContent = activeObj.name.split('—')[0].trim();
      currentModelIcon.textContent = activeObj.provider === 'local' ? (activeObj.id.includes('3b') ? '🟢' : (activeObj.id.includes('r1') ? '🟣' : '🔵')) : '☁️';
    }

    availableModels.forEach(m => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'model-item' + (m.id === currentActiveModel ? ' active' : '');
      const icon = m.provider === 'local' ? (m.id.includes('3b') ? '🟢' : (m.id.includes('r1') ? '🟣' : '🔵')) : '☁️';

      item.innerHTML = `
        <div class="model-item-top">
          <span class="model-item-title">${icon} ${m.name}</span>
          <span class="model-item-badge">${m.ram || (m.provider === 'local' ? 'Local' : 'Cloud')}</span>
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
        if (data.ai_configured) {
          aiStatus.className = 'ai-status ok';
          if (data.is_local) {
            aiStatusText.textContent = `Local AI (${data.model_in_use})`;
          } else {
            aiStatusText.textContent = `DeepSeek Cloud (${data.model_in_use || 'chat'})`;
          }
        } else {
          aiStatus.className = 'ai-status warn';
          aiStatusText.textContent = 'Chưa cấu hình API Key / Ollama';
        }
      }
    } catch {
      aiStatus.className = 'ai-status';
      aiStatusText.textContent = 'Mất kết nối server';
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
    const isRagActive = document.getElementById('tab-rag')?.classList.contains('active');
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

    const isRagActive = document.getElementById('tab-rag')?.classList.contains('active');
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
        sessionId = data.session_id;
        localStorage.setItem('cva_session_id', sessionId);
      }

      // Xoá chip tạm và thêm chip chính thức
      removeChipElement(tempId);
      const att = data.attachment;
      pendingAttachments.push(att);
      renderAttachChip(att);
      updateSendButton();
    } catch (err) {
      removeChipElement(tempId);
      alert(`Không thể đọc tệp ${file.name}: ${err.message}`);
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
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          action: action,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Lỗi kết nối máy chủ');
      }

      const data = await res.json();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem('cva_session_id', sessionId);
      }

      thinkingEl.remove();
      appendAssistantMessage(data);
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
        const res = await fetch('/api/chat/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
        });
        const d = await res.json();
        sessionId = d.session_id;
        localStorage.setItem('cva_session_id', sessionId);
      } catch {}

      messagesContainer.innerHTML = '';
      pendingAttachments = [];
      attachList.innerHTML = '';
      input.value = '';
      resizeInput();
      if (welcome) welcome.style.display = 'block';
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
      <div class="avatar thinking">★</div>
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
    avatar.textContent = '★';

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
          // Vô hiệu hoá tất cả nút trong nhóm sau khi đã bấm
          actionsDiv.querySelectorAll('.act-btn').forEach((b) => (b.disabled = true));
          sendMessage('', act.id);
        });
        actionsDiv.appendChild(btn);
      });
      content.appendChild(actionsDiv);
    }

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
  // 7. ĐIỀU KHIỂN 05 TABS & TẢI DỮ LIỆU QUẢN TRỊ (SỔ VIỆC, KPI, RAG, DANH BẠ)
  // ============================================================================
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabContents = document.querySelectorAll('.tab-content');

  navTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      navTabs.forEach(b => b.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));

      btn.classList.add('active');
      const activeContent = document.getElementById(targetTab);
      if (activeContent) activeContent.classList.add('active');

      if (targetTab === 'tab-tasks') loadTasks();
      if (targetTab === 'tab-rag') {
        loadRagStats();
        loadRagDocuments();
      }
      if (targetTab === 'tab-kpis') loadKpis();
      if (targetTab === 'tab-directory') loadDirectory();
    });
  });

  // --- SỔ NHIỆM VỤ ---
  const tasksTableBody = document.getElementById('tasksTableBody');
  const filterTaskUnit = document.getElementById('filterTaskUnit');
  const filterTaskStatus = document.getElementById('filterTaskStatus');
  const btnRefreshTasks = document.getElementById('btnRefreshTasks');

  if (filterTaskUnit) filterTaskUnit.addEventListener('change', loadTasks);
  if (filterTaskStatus) filterTaskStatus.addEventListener('change', loadTasks);
  if (btnRefreshTasks) btnRefreshTasks.addEventListener('click', loadTasks);

  async function loadTasks() {
    if (!tasksTableBody) return;
    tasksTableBody.innerHTML = '<tr><td colspan="7" class="loading-td">Đang tải Sổ nhiệm vụ...</td></tr>';
    try {
      const unit = filterTaskUnit ? filterTaskUnit.value : '';
      const status = filterTaskStatus ? filterTaskStatus.value : '';
      const res = await fetch(`/api/tasks?co_quan=${encodeURIComponent(unit)}&trang_thai=${encodeURIComponent(status)}`);
      const data = await res.json();
      const tasks = data.tasks || [];

      if (tasks.length === 0) {
        tasksTableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px; color:#94a3b8;">Không có nhiệm vụ nào phù hợp với bộ lọc.</td></tr>';
        return;
      }

      tasksTableBody.innerHTML = tasks.map(t => {
        let badgeClass = 'status-pending';
        if (t.trang_thai === 'Đang thực hiện') badgeClass = 'status-inprogress';
        if (t.trang_thai === 'Hoàn thành') badgeClass = 'status-completed';
        if (t.trang_thai === 'Chuyển tiếp tháng sau') badgeClass = 'status-rescheduled';

        const isDone = t.trang_thai === 'Hoàn thành';
        const actionBtn = isDone
          ? '<span style="color:#64748b; font-size:12px;">Đã chốt</span>'
          : `<button class="btn-status-done" onclick="window.markTaskDone('${t.task_id}')">✓ Xong</button>`;

        return `
          <tr>
            <td>
              <div style="font-weight:700; color:#38bdf8;">${escapeHtml(t.task_id)}</div>
              <div style="font-size:11.5px; color:#94a3b8;">${escapeHtml(t.so_hieu_vb || '-')}</div>
            </td>
            <td><b>${escapeHtml(t.co_quan_chu_tri)}</b></td>
            <td>
              <div>${escapeHtml(t.noi_dung_nhiem_vu)}</div>
              ${t.cap_trinh ? `<div style="font-size:11.5px; color:#cbd5e1; margin-top:2px;">Cấp trình: <i>${escapeHtml(t.cap_trinh)}</i></div>` : ''}
            </td>
            <td><code>${escapeHtml(t.deadline_date || '')}</code></td>
            <td><span style="font-size:12px;">${escapeHtml(t.muc_do_uu_tien || 'Bình thường')}</span></td>
            <td><span class="status-badge ${badgeClass}">${escapeHtml(t.trang_thai)}</span></td>
            <td>${actionBtn}</td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tasksTableBody.innerHTML = `<tr><td colspan="7" style="color:#ef4444; padding:20px;">Lỗi tải dữ liệu: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  window.markTaskDone = async function(taskId) {
    try {
      const res = await fetch(`/api/tasks/${taskId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trang_thai: 'Hoàn thành', ket_qua_bao_cao: 'Đã hoàn thành báo cáo' })
      });
      if (res.ok) {
        loadTasks();
      }
    } catch (err) {
      alert('Lỗi cập nhật nhiệm vụ: ' + err.message);
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
        alert('Vui lòng nhập tên chuyên đề mới!');
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
          alert(`✓ Đã thêm chuyên đề mới "${name}" thành công! Chuyên đề này đã được lưu vào hệ thống.`);
          inputNewChuyenDe.value = '';
          if (wrapNewChuyenDe) wrapNewChuyenDe.style.display = 'none';
          await loadThematics(data.thematic.ma_chuyen_de);
        } else {
          alert('Lỗi: ' + (data.detail || 'Không thể tạo chuyên đề'));
        }
      } catch (err) {
        alert('Lỗi kết nối: ' + err.message);
      } finally {
        btnSaveNewChuyenDe.disabled = false;
        btnSaveNewChuyenDe.textContent = '+ Thêm ngay';
      }
    });
  }

  // 2. Tải danh mục văn bản đã duyệt trong kho
  async function loadRagDocuments() {
    if (!ragDocsTableBody) return;
    ragDocsTableBody.innerHTML = '<tr><td colspan="9" class="loading-td">Đang tải danh mục văn bản trong kho...</td></tr>';
    try {
      const res = await fetch('/api/rag/documents');
      if (!res.ok) throw new Error('Không thể lấy danh sách văn bản');
      const d = await res.json();
      const docs = d.documents || [];

      if (docs.length === 0) {
        ragDocsTableBody.innerHTML = '<tr><td colspan="9" class="loading-td">Kho RAG hiện đang trống. Bấm "Nạp văn bản mới" để bắt đầu nạp có kiểm duyệt.</td></tr>';
        return;
      }

      ragDocsTableBody.innerHTML = docs.map(doc => {
        let badgeVongDoi = '<span class="status-badge status-inprogress">Chuyên đề</span>';
        if (doc.nhom_vong_doi === 'CORE_DIRECTIVE') {
          badgeVongDoi = '<span class="status-badge status-completed">Nền tảng</span>';
        } else if (doc.nhom_vong_doi === 'EPHEMERAL_EVENT') {
          badgeVongDoi = '<span class="status-badge status-rescheduled">Sự vụ</span>';
        }

        return `
          <tr>
            <td><b style="color:#38bdf8;">${escapeHtml(doc.so_hieu_vb || '-')}</b></td>
            <td><span class="badge-theloai">${escapeHtml(doc.the_loai_vb || doc.the_loai || '-')}</span></td>
            <td>${escapeHtml(doc.co_quan_ban_hanh || '-')}</td>
            <td><code>${escapeHtml(doc.ngay_ban_hanh || '-')}</code></td>
            <td>${badgeVongDoi}</td>
            <td><span class="badge-theloai" style="background: rgba(56, 189, 248, 0.12); color: #38bdf8; font-weight:600;">${escapeHtml(doc.ten_chuyen_de || doc.ma_chuyen_de || 'Chung')}</span></td>
            <td style="max-width: 280px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" title="${escapeHtml(doc.trich_yeu || '')}">${escapeHtml(doc.trich_yeu || '-')}</td>
            <td style="text-align: center;"><span class="badge-theloai" style="background: rgba(255,255,255,0.08); color: #cbd5e1; font-weight: 600;">${doc.chunk_count || 0}</span></td>
            <td style="text-align: center; white-space: nowrap;">
              <button class="btn-edit-doc" onclick="window.openRagDocDetail('${escapeHtml(doc.doc_id)}')" title="Xem chi tiết các đoạn trích và chỉnh sửa văn bản">👁️ Sửa</button>
              <button class="btn-delete-doc" onclick="window.deleteRagDocument('${escapeHtml(doc.doc_id)}', '${escapeHtml(doc.so_hieu_vb || '')}')" title="Xoá văn bản này khỏi kho">🗑️</button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      ragDocsTableBody.innerHTML = `<tr><td colspan="9" style="color:#ef4444; padding:20px;">Lỗi: ${escapeHtml(err.message)}</td></tr>`;
    }
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
      alert('Lỗi tải chi tiết văn bản: ' + err.message);
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
        alert('Số hiệu văn bản không được để trống!');
        return;
      }
      if (!trichYeu) {
        alert('Trích yếu không được để trống!');
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
          alert(`✓ Đã cập nhật thành công thông tin văn bản "${updates.so_hieu_vb}"!`);
          closeEditModal();
          loadRagDocuments();
          loadRagStats();
        } else {
          alert('Lỗi cập nhật: ' + (data.detail || 'Lỗi server'));
        }
      } catch (err) {
        alert('Lỗi kết nối: ' + err.message);
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
        alert(data.message || 'Đã xoá văn bản thành công!');
        loadRagStats();
        loadRagDocuments();
      } else {
        alert('Lỗi: ' + (data.detail || 'Không thể xoá văn bản'));
      }
    } catch (err) {
      alert('Lỗi mạng khi xoá văn bản: ' + err.message);
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
          alert('✓ Đã xoá sạch toàn bộ dữ liệu Kho RAG thành công!');
          loadRagStats();
          loadRagDocuments();
          if (ragResultsWrap) ragResultsWrap.innerHTML = '';
        } else {
          alert('Lỗi xoá dữ liệu: ' + (data.detail || 'Lỗi server'));
        }
      } catch (err) {
        alert('Lỗi kết nối: ' + err.message);
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
      alert(`Định dạng tệp "${file.name}" không được hỗ trợ.\nHệ thống chỉ tiếp nhận văn bản: Word (.docx, .doc), PDF (.pdf), Text (.txt, .md).`);
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
        alert('⚠️ Không thể tiếp nhận văn bản:\n\n' + (data.detail || 'Lỗi không xác định'));
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
      alert('Lỗi khi đọc và bóc tách tệp: ' + err.message);
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
        alert('Không có dữ liệu văn bản để nạp!');
        return;
      }

      const soHieu = reviewSoHieu ? reviewSoHieu.value.trim() : '';
      const ngay = reviewNgay ? reviewNgay.value : '';
      const coQuan = reviewCoQuan ? reviewCoQuan.value.trim() : '';
      const trichYeu = reviewTrichYeu ? reviewTrichYeu.value.trim() : '';

      if (!soHieu) {
        alert('Vui lòng nhập Số hiệu văn bản!');
        if (reviewSoHieu) reviewSoHieu.focus();
        return;
      }
      if (!ngay) {
        alert('Vui lòng chọn Ngày ban hành văn bản!');
        if (reviewNgay) reviewNgay.focus();
        return;
      }
      if (!coQuan) {
        alert('Vui lòng nhập Cơ quan ban hành!');
        if (reviewCoQuan) reviewCoQuan.focus();
        return;
      }
      if (!trichYeu) {
        alert('Vui lòng nhập Trích yếu nội dung văn bản!');
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
          alert(`✓ Phê duyệt và nạp văn bản "${payload.so_hieu_vb}" vào Kho RAG thành công! (${chunkCount} đoạn trích)`);
          closeRagModal();
          loadRagStats();
          loadRagDocuments();
        } else {
          alert('⚠️ Lỗi khi lưu văn bản: ' + (data.detail || 'Lỗi hệ thống'));
        }
      } catch (err) {
        alert('Lỗi kết nối khi lưu: ' + err.message);
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

  // --- GIÁM SÁT CHỈ TIÊU KPI ---
  const kpisGrid = document.getElementById('kpisGrid');
  const kpiFilterChips = document.querySelectorAll('[data-kpi-source]');

  kpiFilterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      kpiFilterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      loadKpis(chip.getAttribute('data-kpi-source'));
    });
  });

  async function loadKpis(sourceFilter = '') {
    if (!kpisGrid) return;
    kpisGrid.innerHTML = '<div class="loading-state">Đang tải chỉ tiêu...</div>';

    try {
      const url = sourceFilter ? `/api/kpis?source=${encodeURIComponent(sourceFilter)}` : '/api/kpis';
      const res = await fetch(url);
      const data = await res.json();
      const kpis = data.kpis || [];

      if (kpis.length === 0) {
        kpisGrid.innerHTML = '<div class="empty-state">Không có chỉ tiêu nào.</div>';
        return;
      }

      kpisGrid.innerHTML = kpis.map(k => {
        let badgeClass = 'badge-green';
        let fillClass = 'fill-green';
        if (k.trang_thai_anh_sang === 'VANG') { badgeClass = 'badge-yellow'; fillClass = 'fill-yellow'; }
        if (k.trang_thai_anh_sang === 'DO') { badgeClass = 'badge-red'; fillClass = 'fill-red'; }

        // Tính % tiến độ ước tính
        let percent = 100;
        if (k.chi_tieu_nam_2026 && k.chi_tieu_nam_2026 > 0) {
          percent = Math.min(100, Math.round(((k.gia_tri_hien_tai || 0) / k.chi_tieu_nam_2026) * 100));
        }

        return `
          <div class="kpi-card">
            <div class="kpi-header">
              <div class="kpi-title">${escapeHtml(k.ten_chi_tieu)}</div>
              <span class="kpi-badge ${badgeClass}">${escapeHtml(k.trang_thai_anh_sang || 'XANH')}</span>
            </div>
            <div class="kpi-value-row">
              <span>Mục tiêu 2026: <b class="kpi-target">${escapeHtml(k.bieu_thuc_chi_tiet || (k.chi_tieu_nam_2026 + ' ' + k.don_vi_tinh))}</b></span>
              <span>Hiện tại: <b style="color:#38bdf8;">${k.gia_tri_hien_tai ? k.gia_tri_hien_tai + ' ' + k.don_vi_tinh : 'Đạt'}</b></span>
            </div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress-fill ${fillClass}" style="width: ${percent}%;"></div>
            </div>
            <div class="kpi-note">Phụ trách: ${escapeHtml(k.co_quan_phu_trach || 'UBND xã')}</div>
          </div>
        `;
      }).join('');
    } catch (err) {
      kpisGrid.innerHTML = `<div style="color:#ef4444; padding:20px;">Lỗi tải chỉ tiêu: ${escapeHtml(err.message)}</div>`;
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

  // Khởi động
  checkStatus();
  loadModels();
  updateSendButton();
});

