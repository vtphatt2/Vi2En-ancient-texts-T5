const sourceText = document.getElementById('sourceText');
const translatedText = document.getElementById('translatedText');

let timeout = null;

sourceText.addEventListener('input', function() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        const text = sourceText.value.trim();
        if (text.length > 0) {
            fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                let translation = data.translation;
                
                if (typeof translation === 'string' && translation.startsWith("en:")) {
                    translation = translation.substring(3).trim(); 
                }
                
                translatedText.value = translation;
            })
            .catch(error => {
                console.error('Error:', error);
                translatedText.value = 'Có lỗi xảy ra khi dịch.';
            });
        } else {
            translatedText.value = '';
        }
    }, 500); 
});
