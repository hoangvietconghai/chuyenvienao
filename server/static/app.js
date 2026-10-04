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

  // Kéo thả tệp trên toàn cửa sổ
  let dragCounter = 0;
  window.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragCounter++;
    dropOverlay.classList.add('show');
  });

  window.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      dropOverlay.classList.remove('show');
    }
  });

  window.addEventListener('dragover', (e) => e.preventDefault());

  window.addEventListener('drop', async (e) => {
    e.preventDefault();
    dragCounter = 0;
    dropOverlay.classList.remove('show');
    const files = Array.from(e.dataTransfer?.files || []);
    for (const f of files) {
      await uploadFile(f);
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

  // Khởi động
  checkStatus();
  loadModels();
  updateSendButton();
});
