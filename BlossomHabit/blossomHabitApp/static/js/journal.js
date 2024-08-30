document.addEventListener('DOMContentLoaded', function() {

    var imagine = '';
    // formatam data curenta si o afisam in elementele aferente
    var today = new Date();
    var dateString = today.toLocaleDateString('ro-RO', {year: 'numeric', month: 'numeric', day: 'numeric' });
    //var dateString2 = today.toISOString().split('T')[0];

    var dateDisplays = document.querySelectorAll('.date-display-left');
    var dateDisplays2 = document.querySelectorAll('.date-display-right');
    
    dateDisplays.forEach(function(display) {
        display.textContent = dateString;
    });

    dateDisplays2.forEach(function(display) {
        display.textContent = dateString;
    });

    const emojiPopup = document.getElementById('emoji-popup');
    const emojiContainer = document.getElementById('emoji-container');
    const emojiArea = document.querySelector('.emoji-area');
    const emojiIds = new Set();
    let emojiCount = 0;

    document.querySelector('.add-emoji-btn').addEventListener('click', function() {
        emojiCount = 0;
        emojiIds.clear();
        fetch('/get_emojis/')
        .then(response => response.json())
        .then(data => {
            emojiArea.innerHTML = '';
            emojiContainer.innerHTML = '';
            data.emojis.forEach(emoji => {
                const img = document.createElement('img');
                img.src = emoji.image_url;
                img.alt = emoji.status;
                img.style.width = '40px';
                img.style.margin = '5px';
                img.style.cursor = 'pointer';
                img.onclick = () => addEmojiToJournal(emoji.image_url, emoji.id);
                emojiContainer.appendChild(img);
            });
            emojiPopup.style.display = 'block';
        })
        .catch(error => console.error('Error loading emojis:', error));
    });

    function addEmojiToJournal(emojiUrl, emojiId) {
        if (emojiIds.has(emojiId)) {
            alert("This emoji was already added");
            return;
        }
        if (emojiCount >= 5) {
            alert("There are already 5 emojis");
            return;
        }
        const emojiImg = document.createElement('img');
        emojiImg.src = emojiUrl;
        emojiImg.style.width = '25px';
        emojiImg.style.height = '25px';
        emojiArea.appendChild(emojiImg);
        emojiCount++;

        emojiIds.add(emojiId);
    }

    document.getElementById('emoji-popup').querySelector('.close-emoji-popup').addEventListener('click', function() {
        emojiPopup.style.display = 'none';
    });

    document.querySelector('.add-text-btn').addEventListener('click', function() {
        document.getElementById('text-popup').style.display = 'block';
        
        document.getElementById('text-input').value = '';
        
        document.getElementById('text-input').value += document.querySelector('.journal-text-left').textContent.trim() +
            document.querySelector('.journal-text-right').textContent.trim();

        document.querySelector('.journal-text-left').textContent = '';
        document.querySelector('.journal-text-right').textContent = '';
    });
    
    window.saveText = function() {
        const maxLeftPage = 700;
        const maxRightPage = 750;
        const textInput = document.getElementById('text-input');
        const text = textInput.value;
        textInput.value = '';
    
        const leftPage = document.querySelector('.page.left-page .journal-text-left');
        const rightPage = document.querySelector('.page.right-page .journal-text-right');
    
        leftPage.textContent = '';
        rightPage.textContent = '';
    
        let remainingText = text;
    
        if (remainingText.length > maxLeftPage) {
            leftPage.textContent = remainingText.substring(0, maxLeftPage);
            remainingText = remainingText.substring(maxLeftPage);
        } else {
            leftPage.textContent = remainingText;
            remainingText = '';
        }
    
        if (remainingText.length > 0) {
            if (remainingText.length > maxRightPage) {
                rightPage.textContent = remainingText.substring(0, maxRightPage);
            } else {
                rightPage.textContent = remainingText;
            }
        }
    
        document.getElementById('text-popup').style.display = 'none';
    
        document.querySelector('.journal-text-left').textContent = leftPage.textContent;
        document.querySelector('.journal-text-right').textContent = rightPage.textContent;
    };
    
    document.getElementById('text-input').addEventListener('input', function() {
        const maxChars = 700 + 750;
        let charCount = document.getElementById('char-count');
        let currentLength = this.value.length;
    
        if (currentLength > maxChars) {
            this.value = this.value.substring(0, maxChars);
            currentLength = maxChars;
        }
    
        charCount.textContent = `${currentLength}/${maxChars}`;
    });    
    
    document.querySelector('.add-images-btn').addEventListener('click', function() {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', function(event) {
        const file = event.target.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const imgDay = new Image();
            imgDay.src = e.target.result;

            imagine = e.target.result;

            imgDay.width = 100;
            imgDay.height = 100;

            const imgcontainer = document.querySelector('.image-container');
            imgcontainer.innerHTML = '';
            imgcontainer.appendChild(imgDay);
        };
        reader.readAsDataURL(file);
    });

    function saveJournal() {
        console.log('am intrat in saveJournal');
        const date = document.querySelector('.date-display-left').textContent.trim();
        const textLeft = document.querySelector('.page.left-page .journal-text-left').textContent.trim();
        const textRight = document.querySelector('.page.right-page .journal-text-right').textContent.trim();
        const text = textLeft + textRight;

        const emojis = Array.from(emojiIds).join(',');

        document.getElementById('journal-date').value = date;
        document.getElementById('journal-text').value = text;
        document.getElementById('journal-emojis').value = emojis;
        document.getElementById('journal-image').value = imagine;

        document.getElementById('journal-form').submit();
    }

    document.getElementById('journal-form').addEventListener('submit', function(event) {
        event.preventDefault();
        saveJournal();
    });
    
    setTimeout(function() {
        var messagesArea = document.querySelector('.messages-area');
        messagesArea.innerHTML = '';
    }, 7000);
});

function closeEmojiPopup() {
    document.getElementById('emoji-popup').style.display = 'none';
}

function closeTextPopup() {
    document.getElementById('text-popup').style.display = 'none';
}
