// Auto-set today's date on the add expense form
document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.querySelector('input[name="date"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    // Auto-format all amounts using browser locale and currency
    const locale = navigator.language || 'en-IN';
    const currency = localeToCurrency(locale);

    document.querySelectorAll('[data-amount]').forEach(el => {
        const amount = parseFloat(el.dataset.amount);
        if (isNaN(amount)) return;
        el.textContent = new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 2
        }).format(amount);
    });
});

function localeToCurrency(locale) {
    const map = {
        'en-IN': 'INR', 'hi': 'INR', 'bn': 'INR',
        'en-US': 'USD', 'en-CA': 'CAD', 'en-GB': 'GBP',
        'en-AU': 'AUD', 'en-NZ': 'NZD', 'en-SG': 'SGD',
        'de': 'EUR', 'fr': 'EUR', 'it': 'EUR', 'es': 'EUR',
        'pt-BR': 'BRL', 'pt': 'EUR',
        'ja': 'JPY', 'ko': 'KRW', 'zh': 'CNY',
        'ar': 'SAR', 'ar-AE': 'AED', 'ar-EG': 'EGP',
        'tr': 'TRY', 'ru': 'RUB', 'pl': 'PLN',
        'th': 'THB', 'id': 'IDR', 'ms': 'MYR',
        'fil': 'PHP', 'vi': 'VND', 'uk': 'UAH',
        'nl': 'EUR', 'sv': 'SEK', 'no': 'NOK', 'da': 'DKK',
        'fi': 'EUR', 'cs': 'CZK', 'hu': 'HUF', 'ro': 'RON',
        'he': 'ILS', 'af': 'ZAR', 'en-ZA': 'ZAR',
        'en-PK': 'PKR', 'ur': 'PKR',
        'bn-BD': 'BDT', 'si': 'LKR',
    };
    // Try full locale first, then language prefix
    return map[locale] || map[locale.split('-')[0]] || 'USD';
}