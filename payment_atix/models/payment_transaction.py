from odoo import models, fields, api, _
import json
import requests
import logging
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment_atix import const

_logger = logging.getLogger(__name__)


URL_ATIX_JS = {
    "test":"https://gateway.atix.com.pe/cdn/TEST/v1.1/ATIXPaymentGateway.min.js",
    "enabled":"https://gateway.atix.com.pe/cdn/gbcpepaymentjs/V1.1/ATIXPaymentGateway.min.js"
}

URL_ATIX_API = {
    "test":"https://gateway.atix.com.pe/PaymentGatewayJWS_Sandbox/Service1.svc",
    "enabled":"https://gateway.atix.com.pe/PaymentGatewayJWS/Service1.svc"
}

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    atix_token = fields.Char("ATIX Token")
    atix_reference_code = fields.Char("Reference Code")

    def _get_processing_values(self):
        res = super(PaymentTransaction, self)._get_processing_values()
        if self.provider_code != 'atix':
            return res
        res.update(tx_id=self.id)
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
        return {}

    def _authenticate_with_atix(self):
        api_key_map = {
            "PEN": self.provider_id.atix_apikey_pen,
            "USD": self.provider_id.atix_apikey_usd,
        }
        api_key = api_key_map.get(self.currency_id.name) or ""

        data_dict = {
            "totalamount": self.amount,
            "currency": self.currency_id.name,
            "reference": self.reference,
            "email": self.partner_email or "",
        }
        payload = json.dumps({
            "Apikey": api_key,
            "Version": "V1.1",
            "Data": json.dumps(data_dict),
        })

        response = requests.post(
            f"{URL_ATIX_API[self.provider_id.state]}/GBCPE_AuthenticateUser",
            headers={"Content-Type": "text/plain"},
            data=payload,
            timeout=30,
        )

        result = response.json()
        redirect_url = result[0].get("Url")
        return redirect_url

    def _request_payment_atix_status(self):
        url = f"{URL_ATIX_API[self.provider_id.state]}/GBCPE_ResultTransaction"

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
                self._post_process()
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
