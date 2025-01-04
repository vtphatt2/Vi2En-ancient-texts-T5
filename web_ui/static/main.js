const sourceText = document.getElementById('sourceText');
const translatedText = document.getElementById('translatedText');

const translatedTextContainer = translatedText.parentElement;
translatedTextContainer.style.position = 'relative';

const loader = document.createElement('div');
loader.className = 'loader';
loader.style.display = 'none';
loader.style.position = 'absolute';
loader.style.top = '45%';
loader.style.left = '50%';
loader.style.transform = 'translate(-50%, -50%)';
loader.style.zIndex = '10'; 

const overlay = document.createElement('div');
overlay.style.position = 'absolute';
overlay.style.top = '0';
overlay.style.left = '0';
overlay.style.width = '100%';
overlay.style.height = '100%';
overlay.style.display = 'none';
overlay.style.zIndex = '5'; 

translatedTextContainer.appendChild(overlay);
translatedTextContainer.appendChild(loader);

let debounceTimer;

sourceText.addEventListener('input', () => {
    if (debounceTimer) {
        clearTimeout(debounceTimer);
    }

    debounceTimer = setTimeout(() => {
        const text = sourceText.value.trim();

        if (text === "") {
            translatedText.value = "";
            overlay.style.display = 'none';
            loader.style.display = 'none';
            return;
        }

        overlay.style.display = 'block';
        loader.style.display = 'inline-block';

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
            translatedText.value = 'Đã xảy ra lỗi khi dịch văn bản.';
        })
        .finally(() => {
            overlay.style.display = 'none';
            loader.style.display = 'none';
        });

    }, 500);
});


const copyButton = document.getElementById('copyButton');

copyButton.addEventListener('click', () => {
    const textToCopy = translatedText.value;

    if (textToCopy) {
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                const originalSrc = copyButton.querySelector('img').src;
                copyButton.querySelector('img').src = "/static/check.svg";

                setTimeout(() => {
                    copyButton.querySelector('img').src = originalSrc;
                }, 1500);

                const toast = document.getElementById('toast');
                toast.className = 'toast show';
                setTimeout(() => { toast.className = toast.className.replace('show', ''); }, 3000);
            })
    } else {
        alert('There is no text to copy.');
    }
});
