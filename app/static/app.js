const api = '/api'; let sessionId = null;
const $ = (s) => document.querySelector(s);
async function request(path, options) { const r = await fetch(api + path, options); if (!r.ok) throw new Error((await r.json()).detail || 'Request failed'); return r.status === 204 ? null : r.json(); }
function message(item) { const el = document.createElement('div'); el.className = `message ${item.role}`; el.textContent = item.content; $('#messages').append(el); $('#messages').scrollTop = $('#messages').scrollHeight; }
async function loadSessions() { const sessions = await request('/sessions'); const box = $('#sessions'); box.replaceChildren(); sessions.forEach(s => { const b = document.createElement('button'); b.className = `session ${s.id === sessionId ? 'active' : ''}`; b.textContent = s.title; b.onclick = () => openSession(s.id); box.append(b); }); }
async function openSession(id) { sessionId = id; const messages = await request(`/sessions/${id}/messages`); $('#messages').replaceChildren(); messages.length ? messages.forEach(message) : $('#messages').innerHTML = '<div class="empty">Ask your first database question.</div>'; await loadSessions(); }
async function newChat() { const s = await request('/sessions', {method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); await openSession(s.id); }
$('#new-chat').onclick = () => newChat().catch(showError);
$('#sync').onclick = async () => { try { $('#status').textContent = 'Syncing schema…'; const data = await request('/schema'); $('#schema').textContent = data.content; $('#schema').classList.remove('hidden'); $('#status').textContent = 'Schema synced successfully.'; } catch(e) { showError(e); } };
$('#composer').onsubmit = async (e) => { e.preventDefault(); const input = $('#question'); const content = input.value.trim(); if (!content) return; try { if (!sessionId) await newChat(); $('#messages .empty')?.remove(); message({role:'user',content}); input.value=''; $('#status').textContent='Gemini is thinking…'; const data = await request(`/sessions/${sessionId}/messages`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})}); message(data.assistant_message); $('#status').textContent='Ready'; await loadSessions(); } catch(e) { showError(e); } };
function showError(e) { $('#status').textContent = e.message; }
loadSessions().catch(showError);
