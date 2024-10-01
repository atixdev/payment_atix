from odoo import models, fields, api, _
import json
import requests
import logging
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment_atix import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    atix_token = fields.Char("ATIX Token")
    atix_reference_code = fields.Char("Reference Code")

    def _get_processing_values(self):
        res = super(PaymentTransaction, self)._get_processing_values()
        API_KEY = {
            "PEN": self.provider_id.atix_apikey_pen,
            "USD": self.provider_id.atix_apikey_usd
        }
        res.update(atix_apikey=API_KEY.get(self.currency_id.name, "*") or "*", tx_id=self.id)
        return res

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Paypal-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'atix':
            return res

        API_KEY = {
            "PEN": self.provider_id.atix_apikey_pen,
            "USD": self.provider_id.atix_apikey_usd
        }

        res = {
            "User": "wzzzGE38zPk5pUKWd7jhN",
            "Password": "YkSzED4ty92BjMa2SXYsF",
            "Version": "V1.1",
            "api_url": "https://gateway.atix.com.pe/PaymentGatewayJWS/Service1.svc/GBCPE_AuthenticateUser",
            "Apikey": API_KEY.get(self.currency_id.name, "*") or "*",
            "Data": json.dumps({"country": self.currency_id.name,
                                "totalamount": str(self.amount),
                                "reference": self.reference,
                                "phone": "",
                                "urlorigi": "http://localhost:9007",
                                "mobile": "", "typeconection": {},
                                "protocol": "http:",
                                "navigator": "Chrome 119",
                                "jsondata": "",
                                "reference2": ""})
        }

        return res

    def _request_payment_atix_status(self):
        url = "https://gateway.atix.com.pe/PaymentGatewayJWS/Service1.svc/GBCPE_ResultTransaction"

        payload = json.dumps({"Token": self.atix_token})
        headers = {
            'content-type': 'text/plain',
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            data = response.json()[0]
            if data.get("ResultCode", False) == "00":
                self.write({"atix_reference_code": data.get("ReferenceCode")})
                self._set_done()
                self._finalize_post_processing()
            elif data.get("ReferenceCode", False) and data.get("ResultCode", False) == '-99':
                self.write({"atix_reference_code": data.get("ReferenceCode")})
                self._set_canceled(
                    "Transacción con código de referencia {}, ha sido cancelada.".format(data.get("ReferenceCode")))

        else:
            return {}

    def action_request_payment_atix_status(self):
        for record in self:
            record._request_payment_atix_status()

    @api.model
    def cron_request_payment_atix_status(self):
        for record in self.sudo().search(
                [("provider_id.code", "=", "atix"), ("atix_token", "!=", False), ("atix_reference_code", "=", False),
                 ("create_date", ">=", fields.Datetime.now() - timedelta(hours=6))]):
            record._request_payment_atix_status()
