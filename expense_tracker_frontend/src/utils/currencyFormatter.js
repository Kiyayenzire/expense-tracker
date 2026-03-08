

export const formatCurrency = (amount, currency = "EUR", locale = "de-DE") => {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
  }).format(amount);
};


