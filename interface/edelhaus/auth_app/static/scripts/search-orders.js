document.addEventListener('DOMContentLoaded', function () {
    const searchBtn = document.querySelector('.btn.search');
    const searchPopup = document.getElementById('searchPopup');
    const searchInput = document.getElementById('searchOrderId');
    const applySearchBtn = document.getElementById('applySearch');
    const cancelSearchBtn = document.getElementById('cancelSearch');
    const tableRows = document.querySelectorAll('.orders-table tbody tr');

    // Открыть попап поиска
    searchBtn.addEventListener('click', function (e) {
        e.preventDefault();
        searchInput.value = '';
        searchPopup.style.display = 'flex';
    });

    // Закрыть попап
    cancelSearchBtn.addEventListener('click', function () {
        searchPopup.style.display = 'none';
    });

    // Применить поиск
    applySearchBtn.addEventListener('click', performSearch);

    // Также поддерживать Enter в поле ввода
    searchInput.addEventListener('keyup', function (e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    function performSearch() {
        const query = searchInput.value.trim();

        tableRows.forEach(row => {
            // Берем номер заказа из первой ячейки (order_id)
            const orderIdCell = row.cells[0];
            const orderId = orderIdCell ? orderIdCell.textContent.trim() : '';

            if (query === '') {
                row.style.display = ''; // показать все
            } else if (orderId === query) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });

        searchPopup.style.display = 'none';
    }
});