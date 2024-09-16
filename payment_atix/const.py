# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Currency codes of the currencies supported by Mercado Pago in ISO 4217 format.
# See https://api.mercadopago.com/currencies. Last seen online: 24 November 2022.
SUPPORTED_CURRENCIES = [
    'PEN',  # Sol
    'USD',  # US Dollars
]

# The codes of the payment methods to activate when Mercado Pago is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'gbc'
]

# Mapping of payment method codes to Mercado Pago codes.
PAYMENT_METHODS_MAPPING = {
    'card': 'debit_card,credit_card,prepaid_card'
}

# Mapping of transaction states to Mercado Pago payment statuses.
# See https://www.mercadopago.com.mx/developers/en/reference/payments/_payments_id/get.
TRANSACTION_STATUS_MAPPING = {
    'pending': ('pending', 'in_process', 'in_mediation'),
    'done': ('approved', 'refunded'),
    'canceled': ('cancelled', 'null'),
}
