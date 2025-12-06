// Форматирование числа: 1234567 → "1.234.567 ₽"
function formatCurrency(amount) {
    if (amount === 0) return '';
    return amount.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + " ₽";
}

function recalculateTotal() {
    let total = 0;
    const rows = document.querySelectorAll('.order-item-row');

    rows.forEach(row => {
        const select = row.querySelector('select[name="product_id[]"]');
        const quantityInput = row.querySelector('input[name="quantity[]"]');
        if (!select || !quantityInput) return;

        const selectedOption = select.selectedOptions[0];
        if (select.value && quantityInput.value) {
            const price = parseFloat(selectedOption?.dataset?.price) || 0;
            const quantity = parseInt(quantityInput.value) || 0;
            total += price * quantity;
        }
    });

    const totalDisplay = document.getElementById('totalDisplay');
    const totalInput = document.getElementById('order_total');

    if (total > 0) {
        totalDisplay.value = formatCurrency(total);
        totalInput.value = total.toFixed(2);
    } else {
        totalDisplay.value = '';
        totalInput.value = '';
    }
}

function addItemRow() {
    const container = document.getElementById('orderItems');
    const firstRow = container.querySelector('.order-item-row');
    if (!firstRow) return;

    const newRow = firstRow.cloneNode(true);
    const select = newRow.querySelector('select');
    const input = newRow.querySelector('input[type="number"]');
    const removeBtn = newRow.querySelector('.btn-remove-item');

    select.value = '';
    input.value = 1;

    select.onchange = null;
    input.oninput = null;
    removeBtn.onclick = null;

    container.appendChild(newRow);
    recalculateTotal();
}

function removeItemRow(button) {
    const rows = document.querySelectorAll('.order-item-row');
    if (rows.length > 1) {
        button.closest('.order-item-row').remove();
        recalculateTotal();
    } else {
        alert('Нужен хотя бы один товар в заказе.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('orderItems');

    container.addEventListener('change', function(e) {
        if (e.target.matches('select[name="product_id[]"]')) {
            recalculateTotal();
        }
    });

    container.addEventListener('input', function(e) {
        if (e.target.matches('input[name="quantity[]"]')) {
            recalculateTotal();
        }
    });

    container.addEventListener('click', function(e) {
        if (e.target.matches('.btn-remove-item')) {
            removeItemRow(e.target);
        }
    });

    document.getElementById('addItemBtn').addEventListener('click', addItemRow);
    recalculateTotal();
});