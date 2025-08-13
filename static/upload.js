// Image upload and preview logic for chat

document.addEventListener('DOMContentLoaded', function() {
    // Add image upload button and file input to the main chat form
    const form = document.getElementById('form');
    const input = document.getElementById('input');
    const uploadBtn = document.createElement('button');
    uploadBtn.type = 'button';
    uploadBtn.id = 'upload-btn';
    uploadBtn.textContent = '📷';
    uploadBtn.title = 'Upload image';
    const imageInput = document.createElement('input');
    imageInput.type = 'file';
    imageInput.id = 'image-upload';
    imageInput.accept = 'image/*';
    imageInput.style.display = 'none';
    form.appendChild(uploadBtn);
    form.appendChild(imageInput);

    uploadBtn.addEventListener('click', () => imageInput.click());

    imageInput.addEventListener('change', function() {
        if (!imageInput.files.length) return;
        const file = imageInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.url) {
                // Send image URL as a chat message
                if (window.socket) {
                    window.socket.emit('chat', { text: data.url });
                } else if (typeof socket !== 'undefined') {
                    socket.emit('chat', { text: data.url });
                }
            } else {
                alert(data.error || 'Upload failed');
            }
        })
        .catch((err) => {
            alert('Upload failed: ' + (err && err.message ? err.message : err));
            console.error('Upload failed:', err);
        });
        imageInput.value = '';
    });
});
