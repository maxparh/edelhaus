function showOrderItems(orderId) {
    const popup = document.getElementById('deletePopup');
    const message = document.getElementById('popupMessage');

    // Сохраняем оригинальное содержимое (для восстановления)
    const originalHTML = message.innerHTML;

    // Показываем загрузку
    message.innerHTML = '<p>Загрузка состава заказа...</p>';
    popup.style.display = 'flex';

    // Загружаем данные
    fetch(`/orders/items/${orderId}/`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        // Подменяем содержимое попапа
        popup.querySelector('.popup-content h3').textContent = `Состав заказа №${orderId}`;
        message.innerHTML = data.html;

        // Скрываем кнопку "Удалить"
        const buttons = popup.querySelector('.popup-buttons');
        if (buttons) {
            buttons.style.display = 'none';
        }
    })
    .catch(() => {
        message.innerHTML = '<p>Ошибка загрузки состава заказа.</p>';
    });

    // Закрытие
    function restoreAndClose() {
        // Восстанавливаем исходный вид попапа
        if (popup.querySelector('.popup-content h3')) {
            popup.querySelector('.popup-content h3').textContent = 'Подтвердите удаление';
        }
        if (message) {
            message.innerHTML = originalHTML;
        }
        const buttons = popup.querySelector('.popup-buttons');
        if (buttons) {
            buttons.style.display = 'flex';
        }
        popup.style.display = 'none';
    }

    // Временно заменяем обработчики
    const confirmBtn = document.getElementById('confirmDelete');
    const cancelBtn = document.getElementById('cancelDelete');

    const originalConfirm = confirmBtn.onclick;
    const originalCancel = cancelBtn.onclick;

    confirmBtn.onclick = restoreAndClose;
    cancelBtn.onclick = restoreAndClose;

    // Восстановление при клике вне окна
    const originalPopupClick = popup.onclick;
    popup.onclick = function(e) {
        if (e.target === popup) {
            restoreAndClose();
        }
    };
}