// Auto-set today's date on the add expense form
document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.querySelector('input[name="date"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
});