from odoo import models,fields,api
import logging
import requests
from odoo.addons.payment_atix import const
from werkzeug import urls
from urllib.parse import urlencode
import json
_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(selection_add=[('atix', 'ATIX')], ondelete={'atix': 'set default'})

    atix_apikey_pen = fields.Text("API KEY (PEN)", required_if_provider="atix", groups="base.group_system")
    atix_apikey_usd = fields.Text("API KEY (USD)", required_if_provider="atix", groups="base.group_system")

    payment_atix_return_url = fields.Text("URL Status", compute="_compute_payment_atix_return_url", help="Copiar esta URL en el campo 'Return URL' de la configuración de ATIX")

    def _compute_payment_atix_return_url(self):
        if not self.website_id.exists():
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        else:
            base_url = self.website_id.domain

        for record in self:
            record.payment_atix_return_url = base_url+"/payment_atix/status/{{{tokenid}}}"

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'atix':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'atix':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
    
    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'atix').update({
            'support_manual_capture': 'full_only',
            'support_refund': "partial",
        })