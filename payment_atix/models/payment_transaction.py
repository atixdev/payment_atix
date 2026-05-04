from odoo import models, fields, api, _
import json
import requests
import logging
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment_atix import const

_logger = logging.getLogger(__name__)

# SPEC-001: URLs y configuración del gateway ATIX.
# Documentación oficial: https://docs.atix.com.pe/apis/venta-online.html
# El payload solo requiere Apikey, Version y Data (JSON string).
# User/Password eran del SDK legacy ATIXPaymentGateway.min.js (obsoleto).
_ATIX_AUTHENTICATE_URL = (
    "https://gateway.atix.com.pe/PaymentGatewayJWS/Service1.svc/GBCPE_AuthenticateUser"
)
_ATIX_RESULT_URL = (
    "https://gateway.atix.com.pe/PaymentGatewayJWS/Service1.svc/GBCPE_ResultTransaction"
)
_ATIX_REQUEST_TIMEOUT = 30  # segundos


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    atix_token = fields.Char("ATIX Token")
    atix_reference_code = fields.Char("Reference Code")

    # -------------------------------------------------------------------------
    # SPEC-001 §3.2.1 — _get_processing_values
    # Solo se pasa tx_id al frontend. Las credenciales y datos sensibles
    # ya no se incluyen en el payload enviado al navegador.
    # -------------------------------------------------------------------------
    def _get_processing_values(self):
        res = super(PaymentTransaction, self)._get_processing_values()
        if self.provider_code != 'atix':
            return res
        # tx_id es el único valor que el JS necesita para llamar al endpoint
        # server-side /payment/atix/authenticate
        res.update(tx_id=self.id)
        return res

    # -------------------------------------------------------------------------
    # SPEC-001 §3.2.2 — _get_specific_rendering_values
    # El flujo ahora es "direct" (controlado por JS) y la autenticación ocurre
    # server-side, por lo que el template de redirect ya no se usa.
    # Se retorna dict vacío para ATIX.
    # -------------------------------------------------------------------------
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'atix':
            return res
        # Flujo directo: no se necesitan valores de rendering para el template
        return {}

    # -------------------------------------------------------------------------
    # SPEC-001 §3.2.3 — _authenticate_with_atix
    # Método interno que realiza la llamada server-side a GBCPE_AuthenticateUser.
    # Retorna (token, redirect_url) o lanza una excepción en caso de error.
    # -------------------------------------------------------------------------
    def _authenticate_with_atix(self):
        """
        Llama al endpoint GBCPE_AuthenticateUser desde el servidor.
        Esquema según documentación oficial: https://docs.atix.com.pe/apis/venta-online.html

        :return: redirect_url (str) — URL a la que redirigir al tarjetahabiente
        :raises UserError: si el gateway retorna un error o no responde
        """
        self.ensure_one()

        api_key_map = {
            "PEN": self.provider_id.atix_apikey_pen,
            "USD": self.provider_id.atix_apikey_usd,
        }
        api_key = api_key_map.get(self.currency_id.name) or ""

        if not api_key:
            raise UserError(
                _("No se encontró una API Key configurada para la moneda %s.")
                % self.currency_id.name
            )

        # Payload oficial ATIX: Apikey + Version + Data (JSON serializado como string).
        # Data contiene: totalamount, currency, reference, email (mínimos requeridos).
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

        _logger.info(
            "payment_atix: Llamando a GBCPE_AuthenticateUser para tx %s (ref: %s, moneda: %s)",
            self.id, self.reference, self.currency_id.name,
        )

        try:
            # Content-Type: text/plain con body JSON (según docs oficiales ATIX)
            response = requests.post(
                _ATIX_AUTHENTICATE_URL,
                headers={"Content-Type": "text/plain"},
                data=payload,
                timeout=_ATIX_REQUEST_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            _logger.error(
                "payment_atix: Timeout al llamar a GBCPE_AuthenticateUser para tx %s", self.id
            )
            raise UserError(
                _("El gateway de ATIX no respondió a tiempo. Intente nuevamente.")
            )
        except requests.exceptions.RequestException as e:
            _logger.error(
                "payment_atix: Error de conexión con GBCPE_AuthenticateUser para tx %s: %s",
                self.id, e,
            )
            raise UserError(
                _("No se pudo conectar con el gateway de ATIX: %s") % str(e)
            )

        if response.status_code != 200:
            _logger.error(
                "payment_atix: GBCPE_AuthenticateUser retornó HTTP %s para tx %s.\nBody: %s",
                response.status_code, self.id, response.text[:2000],
            )
            raise UserError(
                _("El gateway de ATIX retornó un error (HTTP %s). "
                  "Revise el log del servidor para más detalles.") % response.status_code
            )

        try:
            result = response.json()
        except ValueError:
            _logger.error(
                "payment_atix: Respuesta no-JSON de GBCPE_AuthenticateUser para tx %s: %s",
                self.id, response.text,
            )
            raise UserError(_("Respuesta inválida recibida del gateway de ATIX."))

        # La respuesta es un array: [{"Url": "https://..."}]
        if not isinstance(result, list) or not result:
            _logger.error(
                "payment_atix: GBCPE_AuthenticateUser retornó respuesta inesperada para tx %s: %s",
                self.id, result,
            )
            raise UserError(
                _("El gateway de ATIX retornó una respuesta inesperada. "
                  "Verifique la API Key configurada para la moneda %s.")
                % self.currency_id.name
            )

        redirect_url = result[0].get("Url")

        if not redirect_url:
            error_msg = result[0].get("Error") or result[0].get("Message") or str(result[0])
            _logger.error(
                "payment_atix: GBCPE_AuthenticateUser no retornó Url para tx %s: %s",
                self.id, error_msg,
            )
            raise UserError(
                _("Error al iniciar el pago con ATIX: %s") % error_msg
            )

        _logger.info(
            "payment_atix: Autenticación exitosa para tx %s — URL de pago obtenida", self.id
        )
        return redirect_url

    # -------------------------------------------------------------------------
    # Consulta de estado (sin cambios respecto a la versión anterior)
    # -------------------------------------------------------------------------
    def _request_payment_atix_status(self):
        payload = json.dumps({"Token": self.atix_token})
        headers = {
            'content-type': 'text/plain',
        }

        try:
            response = requests.request(
                "POST", _ATIX_RESULT_URL,
                headers=headers, data=payload,
                timeout=_ATIX_REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            _logger.error(
                "payment_atix: Error al consultar estado de tx %s: %s", self.id, e
            )
            return {}

        if response.status_code == 200:
            data = response.json()[0]
            if data.get("ResultCode", False) == "00":
                self.write({"atix_reference_code": data.get("ReferenceCode")})
                self._set_done()
                self._finalize_post_processing()
            elif data.get("ReferenceCode", False) and data.get("ResultCode", False) == '-99':
                self.write({"atix_reference_code": data.get("ReferenceCode")})
                self._set_canceled(
                    "Transacción con código de referencia {}, ha sido cancelada.".format(
                        data.get("ReferenceCode")
                    )
                )
        else:
            return {}

    def action_request_payment_atix_status(self):
        for record in self:
            record._request_payment_atix_status()

    @api.model
    def cron_request_payment_atix_status(self):
        for record in self.sudo().search(
                [("provider_id.code", "=", "atix"),
                 ("atix_token", "!=", False),
                 ("atix_reference_code", "=", False),
                 ("create_date", ">=", fields.Datetime.now() - timedelta(hours=6))]):
            record._request_payment_atix_status()
