// delete-popup.js

let currentDeleteUrl = null;

function openDeletePopup(id, displayName, deleteUrl) {
    window.currentDeleteUrl = deleteUrl; // 

    const popup = document.getElementById('deletePopup');
    const message = document.getElementById('popupMessage');
    const strong = document.getElementById('clientNamePopup');

    strong.textContent = displayName;
    message.innerHTML = 'Вы уверены, что хотите удалить <strong id="clientNamePopup">' + displayName + '</strong>?';

    popup.style.display = 'flex';
}

function closeDeletePopup() {
    const popup = document.getElementById('deletePopup');
    if (popup) {
        popup.style.display = 'none';
    }
    window.currentDeleteUrl = null; // 
}