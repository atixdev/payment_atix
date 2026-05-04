# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PaymentATIXController(http.Controller):

    # -------------------------------------------------------------------------
    # SPEC-001 §3.1 — Nuevo endpoint de autenticación server-side
    # El navegador ya no llama a GBCPE_AuthenticateUser directamente.
    # Este endpoint recibe el tx_id, llama al gateway desde el servidor,
    # guarda el token y retorna solo la URL de redirección al frontend.
    # -------------------------------------------------------------------------
    @http.route("/payment/atix/authenticate", type="json", auth="public", methods=["POST"], csrf=False)
    def atix_authenticate(self, tx_id, **kwargs):
        """
        Autenticación server-side con el gateway ATIX.

        Recibe: { tx_id: <int> }
        Retorna: { redirect_url: <str> } o { error: <str> }
        """
        try:
            tx_sudo = request.env["payment.transaction"].sudo().browse(tx_id)

            if not tx_sudo.exists():
                _logger.warning("payment_atix: authenticate llamado con tx_id inexistente: %s", tx_id)
                return {"error": _("Transacción no encontrada.")}

            if tx_sudo.provider_code != "atix":
                _logger.warning(
                    "payment_atix: authenticate llamado para proveedor incorrecto: %s (tx %s)",
                    tx_sudo.provider_code, tx_id,
                )
                return {"error": _("Proveedor de pago no válido.")}

            redirect_url = tx_sudo._authenticate_with_atix()

            # El gateway retorna solo la URL — el token está embebido en la URL (?token=...).
            # Lo extraemos para guardarlo y poder consultar el estado posterior.
            token = redirect_url.split("token=")[-1] if "token=" in redirect_url else ""
            tx_sudo.write({"atix_token": token})
            tx_sudo._set_pending()

            return {"redirect_url": redirect_url}

        except UserError as e:
            _logger.error("payment_atix: UserError en authenticate para tx %s: %s", tx_id, e)
            return {"error": str(e)}
        except Exception as e:
            _logger.exception(
                "payment_atix: Error inesperado en authenticate para tx %s: %s", tx_id, e
            )
            return {"error": _("Error interno al procesar el pago. Contacte al administrador.")}

    # -------------------------------------------------------------------------
    # SPEC-001 §3.3.1 — DEPRECADO
    # Este endpoint ya no es necesario con el nuevo flujo server-side.
    # El token ahora lo escribe directamente /payment/atix/authenticate.
    # Se mantiene temporalmente para compatibilidad con clientes JS en caché.
    # ELIMINAR en la siguiente versión del módulo.
    # -------------------------------------------------------------------------
    @http.route("/payment/atix/update_token", type="json", auth="public", methods=["POST"], csrf=False)
    def atix_update_token_deprecated(self, tx_id, token, **kwargs):
        """
        DEPRECADO — SPEC-001: Ya no se usa en el nuevo flujo server-side.
        El token ahora es guardado por /payment/atix/authenticate.
        """
        _logger.warning(
            "payment_atix: /payment/atix/update_token está DEPRECADO y será eliminado. "
            "tx_id=%s — Actualizar el módulo JS en el cliente.", tx_id
        )
        try:
            tx_sudo = request.env["payment.transaction"].sudo().browse(tx_id)
            if tx_sudo.exists() and tx_sudo.provider_code == "atix":
                tx_sudo.write({"atix_token": token})
                tx_sudo._set_pending()
                return True
            return False
        except Exception as e:
            _logger.error("payment_atix: Error en update_token (deprecated): %s", e)
            return False


class WebsiteSaleController(WebsiteSale):

    # NOTA: Este controlador hereda lógica de payment_gbc (método _request_payment_gbc_status).
    # No se modifica en SPEC-001 — documentado como issue independiente en ISSUES_AND_IMPROVEMENTS.md.
    @http.route("/payment_gbc/status/<tokenid>", type="http", auth="public", methods=["GET"], csrf=False)
    def shop_payment_get_status(self, tokenid, **post):
        tx = request.env["payment.transaction"].sudo().search(
            [("gbc_token", "=", tokenid)], limit=1
        )
        if tx.exists():
            tx._request_payment_gbc_status()
            order_id = tx.sale_order_ids[0]
            return request.redirect(f'{order_id.access_url}?access_token={order_id.access_token}')

        return request.redirect("/shop")
