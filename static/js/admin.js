
if (!IS_AUTHENTICATED) {
  const loginBtn  = document.getElementById('loginBtn');
  const loginPass = document.getElementById('loginPass');
  const loginErr  = document.getElementById('loginError');

  async function doLogin() {
    loginErr.textContent = '';
    const username = document.getElementById('loginUser').value;
    const password = loginPass.value;
    try {
      const res  = await fetch(API.login, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (res.ok) {
        window.location.reload();
      } else {
        loginErr.textContent = 'Invalid username or password.';
      }
    } catch {
      loginErr.textContent = 'Connection error. Is the Flask server running?';
    }
  }
  loginBtn.addEventListener('click', doLogin);
  loginPass.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
}

function showSection(id) {
  document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.admin-nav a').forEach(a => a.classList.remove('active'));
  document.getElementById('sec-' + id)?.classList.add('active');
  document.querySelector(`.admin-nav a[data-section="${id}"]`)?.classList.add('active');
  const titles = { dashboard:'Dashboard', portfolio:'Portfolio', messages:'Messages', content:'Site Content' };
  const subs   = { dashboard:'Overview & recent activity', portfolio:'Manage portfolio items', messages:'Client enquiries', content:'Edit website copy' };
  document.getElementById('sectionTitle').textContent = titles[id] || id;
  document.getElementById('sectionSub').textContent   = subs[id]   || '';
  if (id === 'portfolio') loadPortfolio();
  if (id === 'messages')  loadMessages();
  if (id === 'content')   loadContent();
}

document.querySelectorAll('.admin-nav a[data-section]').forEach(a => {
  a.addEventListener('click', () => showSection(a.dataset.section));
});

const THUMB_COLORS = ['#C9B99A','#9EB0A4','#D4C4A8','#8B4A2B','#7A8C6E','#B5A48A','#C4A882','#A8C4B8'];
let editingId = null;

async function loadPortfolio() {
  const res   = await fetch(API.portfolio);
  const items = await res.json();
  document.getElementById('portfolioCount').textContent = items.length;
  document.getElementById('statPortfolio').textContent  = items.length;
  document.getElementById('portfolioList').innerHTML = items.length
    ? items.map((item, i) => `
        <div class="portfolio-item">
          <div class="pi-thumb" style="background:${THUMB_COLORS[i % THUMB_COLORS.length]}"></div>
          <span class="pi-title">${item.title}</span>
          <span class="pi-cat">${item.category}</span>
          <span class="pi-year">${item.year}</span>
          <div class="pi-actions">
            <button class="pi-btn" title="Edit" onclick="openEditModal(${item.id},'${item.title.replace(/'/g,"\\'")}','${item.category}',${item.year},'${(item.description||'').replace(/'/g,"\\'")}',${item.featured})">✎</button>
            <button class="pi-btn del" title="Delete" onclick="deletePortfolioItem(${item.id})">✕</button>
          </div>
        </div>`)
      .join('')
    : '<p class="empty-state">No portfolio items yet. Click + Add Item to create one.</p>';
}

function openAddModal() {
  editingId = null;
  document.getElementById('modalTitle').textContent = 'Add Portfolio Item';
  document.getElementById('piTitle').value    = '';
  document.getElementById('piCat').value      = 'wedding';
  document.getElementById('piYear').value     = new Date().getFullYear();
  document.getElementById('piDesc').value     = '';
  document.getElementById('piFeatured').checked = false;
  document.getElementById('addModal').classList.add('open');
}
function openEditModal(id, title, cat, year, desc, featured) {
  editingId = id;
  document.getElementById('modalTitle').textContent = 'Edit Portfolio Item';
  document.getElementById('piTitle').value    = title;
  document.getElementById('piCat').value      = cat;
  document.getElementById('piYear').value     = year;
  document.getElementById('piDesc').value     = desc;
  document.getElementById('piFeatured').checked = featured;
  document.getElementById('addModal').classList.add('open');
}
function closeModal() {
  document.getElementById('addModal').classList.remove('open');
  editingId = null;
}

document.getElementById('addPortfolioBtn')?.addEventListener('click', openAddModal);
document.getElementById('cancelModalBtn')?.addEventListener('click', closeModal);
document.getElementById('addModal')?.addEventListener('click', e => { if (e.target === document.getElementById('addModal')) closeModal(); });

document.getElementById('savePortfolioBtn')?.addEventListener('click', async () => {
  const title = document.getElementById('piTitle').value.trim();
  if (!title) { alert('Title is required'); return; }
  const payload = {
    title,
    category:    document.getElementById('piCat').value,
    year:        parseInt(document.getElementById('piYear').value),
    description: document.getElementById('piDesc').value.trim(),
    featured:    document.getElementById('piFeatured').checked,
  };
  const url    = editingId ? `${API.portfolio}/${editingId}` : API.portfolio;
  const method = editingId ? 'PUT' : 'POST';
  await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  closeModal();
  loadPortfolio();
});

async function deletePortfolioItem(id) {
  if (!confirm('Delete this portfolio item?')) return;
  await fetch(`${API.portfolio}/${id}`, { method: 'DELETE' });
  loadPortfolio();
}

async function loadMessages() {
  const res  = await fetch(API.messages);
  const msgs = await res.json();
  const unread = msgs.filter(m => !m.is_read).length;
  document.getElementById('msgBadge').textContent  = unread;
  document.getElementById('statUnread').textContent = unread;

  const render = (msg) => `
    <div class="msg-item ${msg.is_read ? '' : 'unread'}" onclick="markRead(${msg.id}, this)">
      <div class="msg-avatar">${msg.name[0]}</div>
      <div class="msg-body">
        <div class="msg-name ${msg.is_read ? '' : 'unread'}">${msg.name}</div>
        <div class="msg-preview">${msg.message.slice(0, 80)}${msg.message.length > 80 ? '…' : ''}</div>
        ${msg.email ? `<div class="msg-preview" style="margin-top:0.2rem">${msg.email}</div>` : ''}
      </div>
      <div class="msg-meta">
        <div class="msg-date">${msg.received_at}</div>
        ${msg.service ? `<span class="msg-service">${msg.service}</span>` : ''}
      </div>
      ${!msg.is_read ? '<div class="unread-dot"></div>' : ''}
    </div>`;

  const html = msgs.length ? msgs.map(render).join('') : '<p class="empty-state">No messages yet.</p>';
  document.getElementById('messageList').innerHTML = html;
  document.getElementById('dashMsgList').innerHTML = msgs.length
    ? msgs.slice(0, 5).map(render).join('')
    : '<p class="empty-state">No messages yet.</p>';
}

async function markRead(id, el) {
  await fetch(`${API.messages}/${id}/read`, { method: 'PATCH' });
  el.classList.remove('unread');
  el.querySelector('.msg-name')?.classList.remove('unread');
  el.querySelector('.unread-dot')?.remove();
  loadMessages();
}

document.getElementById('clearMsgsBtn')?.addEventListener('click', async () => {
  if (!confirm('Delete all messages? This cannot be undone.')) return;
  const res  = await fetch(API.messages);
  const msgs = await res.json();
  await Promise.all(msgs.map(m => fetch(`${API.messages}/${m.id}`, { method: 'DELETE' })));
  loadMessages();
});

async function loadContent() {
  const res  = await fetch(API.content);
  const data = await res.json();
  const map = {
    cfTagline:  'tagline',
    cfHeroSub:  'hero_sub',
    cfAbout:    'about',
    cfEmail:    'contact_email',
    cfPhone:    'contact_phone',
    cfAddress:  'contact_address',
    cfYears:    'stat_years',
    cfProjects: 'stat_projects',
    cfAwards:   'stat_awards',
  };
  Object.entries(map).forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (el && data[key] !== undefined) el.value = data[key];
  });
}

document.getElementById('saveContentBtn')?.addEventListener('click', async () => {
  const map = {
    tagline:         document.getElementById('cfTagline')?.value,
    hero_sub:        document.getElementById('cfHeroSub')?.value,
    about:           document.getElementById('cfAbout')?.value,
    contact_email:   document.getElementById('cfEmail')?.value,
    contact_phone:   document.getElementById('cfPhone')?.value,
    contact_address: document.getElementById('cfAddress')?.value,
    stat_years:      document.getElementById('cfYears')?.value,
    stat_projects:   document.getElementById('cfProjects')?.value,
    stat_awards:     document.getElementById('cfAwards')?.value,
  };
  await fetch(API.content, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(map) });
  const s = document.getElementById('saveSuccess');
  s.style.display = 'inline';
  setTimeout(() => s.style.display = 'none', 2500);
});

if (IS_AUTHENTICATED) {
  loadMessages(); 
}

let selectedItemId   = null;
let selectedItemName = '';
let uploadQueue      = [];  

Object.assign(API, {
  images: (itemId) => `${API.portfolio}/${itemId}/images`,
  image:  (imgId)  => `/api/admin/images/${imgId}`,
});

async function loadUploadItemList() {
  const res   = await fetch(API.portfolio);
  const items = await res.json();
  const list  = document.getElementById('uploadItemList');
  if (!list) return;
  list.innerHTML = items.map(item => `
    <div class="upload-item-row" onclick="selectUploadItem(${item.id}, '${item.title.replace(/'/g,"\\'")}')">
      <div class="upload-item-thumb ph"></div>
      <div class="upload-item-info">
        <div class="upload-item-title">${item.title}</div>
        <div class="upload-item-meta">${item.category} · ${item.year}</div>
      </div>
      <span class="upload-item-count">${item.image_count} photo${item.image_count !== 1 ? 's' : ''}</span>
      <span class="upload-item-arrow">›</span>
    </div>`).join('') || '<p class="empty-state">No portfolio items yet — add some in the Portfolio section first.</p>';
}

function selectUploadItem(id, name) {
  selectedItemId   = id;
  selectedItemName = name;
  document.getElementById('uploadStep1').style.display = 'none';
  document.getElementById('uploadStep2').style.display = 'block';
  document.getElementById('uploadItemName').textContent = name;
  uploadQueue = [];
  renderQueue();
  loadExistingImages(id);
}

document.getElementById('uploadBack')?.addEventListener('click', () => {
  document.getElementById('uploadStep1').style.display = 'block';
  document.getElementById('uploadStep2').style.display = 'none';
  uploadQueue = [];
  renderQueue();
  loadUploadItemList(); 
});

const dropZone  = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone?.addEventListener('click', () => fileInput.click());
dropZone?.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone?.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  addFilesToQueue([...e.dataTransfer.files]);
});
fileInput?.addEventListener('change', () => {
  addFilesToQueue([...fileInput.files]);
  fileInput.value = '';  
});

function addFilesToQueue(files) {
  const allowed = ['image/jpeg','image/png','image/webp','image/gif'];
  files.forEach(f => {
    if (!allowed.includes(f.type)) { alert(`${f.name} is not a supported image type.`); return; }
    if (f.size > 16 * 1024 * 1024)  { alert(`${f.name} exceeds the 16 MB limit.`); return; }
    if (!uploadQueue.find(q => q.name === f.name && q.size === f.size)) {
      uploadQueue.push(f);
    }
  });
  renderQueue();
}

function removeFromQueue(idx) {
  uploadQueue.splice(idx, 1);
  renderQueue();
}

function renderQueue() {
  const qEl      = document.getElementById('uploadQueue');
  const actEl    = document.getElementById('uploadActions');
  const countEl  = document.getElementById('uploadCount');
  if (!qEl) return;

  qEl.innerHTML = uploadQueue.map((f, i) => {
    const url = URL.createObjectURL(f);
    return `
      <div class="queue-item" id="qi-${i}">
        <img src="${url}" class="queue-thumb" alt="${f.name}" />
        <div class="queue-name">${f.name}</div>
        <button class="queue-remove" onclick="removeFromQueue(${i})">✕</button>
      </div>`;
  }).join('');

  const hasFiles = uploadQueue.length > 0;
  actEl.style.display  = hasFiles ? 'flex' : 'none';
  if (countEl) countEl.textContent = uploadQueue.length;
}

document.getElementById('doUploadBtn')?.addEventListener('click', async () => {
  if (!uploadQueue.length || !selectedItemId) return;

  const doBtn   = document.getElementById('doUploadBtn');
  const progWrap = document.getElementById('uploadProgressWrap');
  const progBar  = document.getElementById('uploadProgressBar');
  const progLbl  = document.getElementById('uploadProgressLabel');

  doBtn.disabled = true;
  document.getElementById('uploadActions').style.display = 'none';
  progWrap.style.display = 'block';

  const formData = new FormData();
  uploadQueue.forEach(f => formData.append('files', f));

  let prog = 0;
  const ticker = setInterval(() => {
    prog = Math.min(prog + 5, 85);
    progBar.style.setProperty('--prog', prog + '%');
    progLbl.textContent = `Uploading ${uploadQueue.length} image(s)… ${prog}%`;
  }, 100);

  try {
    const res  = await fetch(API.images(selectedItemId), { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(ticker);

    if (res.ok) {
      progBar.style.setProperty('--prog', '100%');
      progLbl.textContent = `✓ ${data.uploaded} image(s) uploaded successfully!`;
      uploadQueue = [];
      renderQueue();
      setTimeout(() => { progWrap.style.display = 'none'; }, 1800);
      loadExistingImages(selectedItemId);
    } else {
      progLbl.textContent = `Error: ${data.error}`;
      document.getElementById('uploadActions').style.display = 'flex';
    }
  } catch (err) {
    clearInterval(ticker);
    progLbl.textContent = 'Upload failed — check the Flask server is running.';
    document.getElementById('uploadActions').style.display = 'flex';
  }
  doBtn.disabled = false;
});

document.getElementById('clearQueueBtn')?.addEventListener('click', () => {
  uploadQueue = [];
  renderQueue();
});

async function loadExistingImages(itemId) {
  const res    = await fetch(API.images(itemId));
  const images = await res.json();
  const el     = document.getElementById('existingImages');
  const countEl = document.getElementById('existingCount');
  if (!el) return;

  countEl.textContent = `${images.length} image${images.length !== 1 ? 's' : ''}`;

  el.innerHTML = images.length
    ? images.map((img, i) => `
        <div class="existing-img-card" id="eimg-${img.id}">
          <img src="${img.url}" alt="${img.alt_text || ''}" loading="lazy" />
          ${i === 0 ? '<span class="existing-img-cover">Cover</span>' : ''}
          <button class="existing-img-del" onclick="deleteImage(${img.id})" title="Delete image">✕</button>
          <div class="existing-img-footer">
            <input class="existing-alt" type="text" value="${img.alt_text || ''}"
              placeholder="Alt text / caption"
              onchange="updateAlt(${img.id}, this.value)"
              title="Alt text for accessibility & SEO" />
          </div>
        </div>`).join('')
    : '<p class="empty-state">No images uploaded yet for this item.</p>';
}

async function deleteImage(imgId) {
  if (!confirm('Delete this image? This cannot be undone.')) return;
  await fetch(API.image(imgId), { method: 'DELETE' });
  document.getElementById(`eimg-${imgId}`)?.remove();
  loadExistingImages(selectedItemId); 
}

async function updateAlt(imgId, value) {
  await fetch(API.image(imgId), {
    method:  'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ alt_text: value }),
  });
}

const origShowSection = showSection;
const _origShow = showSection;

document.querySelectorAll('.admin-nav a[data-section]').forEach(a => {
  if (a.dataset.section === 'images') {
    a.addEventListener('click', loadUploadItemList);
  }
});
