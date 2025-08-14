document.addEventListener('DOMContentLoaded', function() {
    window.nickname = document.getElementById('me-name').textContent;

    const socket = io(window.location.origin, { transports: ["websocket", "polling"] });
    window.socket = socket;
    const messages = document.getElementById('messages');
    const form = document.getElementById('form');
    const input = document.getElementById('input');
    const typing = document.getElementById('typing');
    const meName = document.getElementById('me-name');
    const peerCountEl = document.getElementById('peer-count');
    // Create side panel for online users
    const sidePanel = document.createElement('div');
    sidePanel.id = 'side-panel';
    sidePanel.style = 'position:fixed;right:0;top:0;height:100vh;width:200px;background:#111827;color:#e5e7eb;padding:16px;box-shadow:-2px 0 8px #0003;z-index:10;overflow-y:auto;';
    sidePanel.innerHTML = '<h3 style="margin-top:0;">Online Users</h3><ul id="user-list" style="list-style:none;padding:0;margin:0;"></ul>';
    document.body.appendChild(sidePanel);
    const userListEl = document.getElementById('user-list');

    function esc(s) {
        return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
    }

    function addMessage(data) {
        const li = document.createElement('li');
        li.className = data.nickname === window.nickname ? 'me' : 'other';
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = `${data.nickname} • ${new Date(data.ts).toLocaleTimeString()}`;
        const body = document.createElement('div');
        let text = data.text;
        // Improved regex: match image URLs with query params and uppercase extensions, and also /uploads/ paths
        const imgUrlRegex = /(https?:\/\/(?:[\w.-]+)\/(?:[\w\-./%]+)\.(?:png|jpg|jpeg|gif|webp)|\/uploads\/[\w\-./%]+\.(?:png|jpg|jpeg|gif|webp))(\?[^\s]*)?/gi;
        let html = '';
        let lastIndex = 0;
        let match;
        let found = false;
        while ((match = imgUrlRegex.exec(text)) !== null) {
            found = true;
            html += esc(text.slice(lastIndex, match.index));
            const url = match[0];
            html += `<img src='${url}' alt='image' style='max-width:200px;max-height:200px;display:block;margin-bottom:4px;' onerror="this.style.display='none'" /><a href='${url}' target='_blank' rel='noopener noreferrer'>${esc(url)}</a>`;
            lastIndex = match.index + url.length;
        }
        html += esc(text.slice(lastIndex));
        // If no image URL was found, still show the text as a link if it looks like a URL
        if (!found) {
            // Basic URL regex for non-image links
            html = html.replace(/(https?:\/\/[\w.-]+\/[\w\-./%?=&]+)/gi, url => `<a href='${url}' target='_blank' rel='noopener noreferrer'>${esc(url)}</a>`);
        }
        body.innerHTML = html;
        li.appendChild(meta); li.appendChild(body);
        messages.appendChild(li);
        window.scrollTo(0, document.body.scrollHeight);
    }

    socket.on('connect', () => {
        socket.emit('join', { nickname: window.nickname });
    });

    socket.on('chat', addMessage);

    socket.on('peerCount', count => {
        peerCountEl.textContent = count + ' online';
    });

    socket.on('user_list', users => {
        userListEl.innerHTML = '';
        users.forEach(nick => {
            const li = document.createElement('li');
            li.textContent = nick;
            userListEl.appendChild(li);
        });
    });

    socket.on('typing', (data) => {
        if (data.state) {
            typing.textContent = `${data.nickname} is typing...`;
        } else {
            typing.textContent = '';
        }
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (!input.value.trim()) return;
        socket.emit('chat', { text: input.value });
        input.value = '';
        socket.emit('typing', { state: false });
    });
});
