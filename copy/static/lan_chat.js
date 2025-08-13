document.addEventListener('DOMContentLoaded', function() {
    window.nickname = document.getElementById('me-name').textContent;

    const socket = io(window.location.origin, { transports: ["websocket", "polling"] });
    const messages = document.getElementById('messages');
    const form = document.getElementById('form');
    const input = document.getElementById('input');
    const typing = document.getElementById('typing');
    const meName = document.getElementById('me-name');
    const peerCountEl = document.getElementById('peer-count');

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
        body.innerHTML = esc(data.text);
        li.appendChild(meta); li.appendChild(body);
        messages.appendChild(li);
        window.scrollTo(0, document.body.scrollHeight);
    }

    socket.on('connect', () => {
        socket.emit('join', { nickname: window.nickname });
    });

    socket.on('chat', addMessage);

    socket.on('peerCount', count => {
        peerCountEl.textContent = count;
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
