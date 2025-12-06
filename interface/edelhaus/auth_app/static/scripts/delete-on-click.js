// delete-on-click.js

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.getElementById('confirmDelete').addEventListener('click', function () {
    const deleteUrl = window.currentDeleteUrl || null;

    if (!deleteUrl) {
        console.error('No delete URL provided');
        alert('Ошибка: не указан URL для удаления.');
        closeDeletePopup();
        return;
    }

    const csrftoken = getCookie('csrftoken');

    fetch(deleteUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => {
        if (response.ok || response.redirected) {
            // Успешно удалено — перезагружаем страницу
            location.reload();
        } else {
            console.error('Server error:', response.status);
            alert('Ошибка при удалении на сервере.');
            closeDeletePopup();
        }
    })
    .catch(error => {
        console.error('Network error:', error);
        alert('Ошибка сети при удалении.');
        closeDeletePopup();
    });
});

document.getElementById('cancelDelete').addEventListener('click', function () {
    closeDeletePopup();
});