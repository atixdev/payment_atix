# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
from odoo.addons.portal.controllers import portal
_logger = logging.getLogger(__name__)


class PaymentATIXController(http.Controller):

    @http.route("/payment/atix/authenticate", type="json", auth="public", methods=["POST"], csrf=False)
    def atix_authenticate(self, tx_id, **kwargs):
        tx_sudo = request.env["payment.transaction"].sudo().browse(tx_id)
        redirect_url = tx_sudo._authenticate_with_atix()

        # El token está embebido en la URL: ?token=...
        token = redirect_url.split("token=")[-1] if "token=" in redirect_url else ""
        tx_sudo.write({"atix_token": token})
        tx_sudo._set_pending()

        return {"redirect_url": redirect_url}

    @http.route("/payment/atix/update_token",type="json",auth="public",methods=["POST"],csrf=False)
    def PaymentATIXUpdateToken(self,tx_id,token):
        try:
            transaction_sudo = request.env["payment.transaction"].sudo()
            transaction_sudo.browse(tx_id).write({"atix_token":token})
            transaction_sudo.browse(tx_id)._set_pending()
            return True
        except Exception as e:
            _logger.info(e)
            return False


class WebsiteSaleController(WebsiteSale):
        

    @http.route("/payment_atix/status/<tokenid>",type="http",auth="public",methods=["GET"],csrf=False)
    def shop_payment_get_status(self, tokenid, **post):
        tx = request.env["payment.transaction"].sudo().search([("atix_token","=",tokenid)],limit=1)
        if tx.exists():
            tx._request_payment_atix_status()
            order_id = tx.sale_order_ids[0]
            return request.redirect(f'{order_id.access_url}?access_token={order_id.access_token}')
        
        return request.redirect("/shop")

