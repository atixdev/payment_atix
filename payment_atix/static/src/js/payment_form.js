/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { Component } from '@odoo/owl';
//import { jsonrpc } from "@web/core/network/rpc_service";
import { rpc, RPCError } from '@web/core/network/rpc';
import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({
    _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== "atix") {
            return this._super(...arguments);
        }

        return rpc("/payment/atix/authenticate", { tx_id: processingValues.tx_id })
            .then((result) => {
                if (result && result.redirect_url) {
                    window.location.href = result.redirect_url;
                } else {
                    const errorMsg = (result && result.error) || _t("Error al procesar el pago con ATIX.");
                    this._displayErrorDialog(_t("Error de Pago"), errorMsg);
                }
            })
            .catch(() => {
                this._displayErrorDialog(
                    _t("Error de Pago"),
                    _t("No se pudo conectar con la pasarela de pago. Intente nuevamente.")
                );
            });
    },
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
            if (providerCode != "atix"){
                return this._super(...arguments)
            }else{
                return this._super(providerCode, paymentOptionId, paymentMethodCode,"direct")
            }
        }
});