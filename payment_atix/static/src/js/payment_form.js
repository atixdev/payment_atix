/** @odoo-module **/

// SPEC-001: Migración a autenticación server-side.
// Se elimina la carga dinámica de ATIXPaymentGateway.min.js y toda llamada
// directa al gateway de ATIX desde el navegador.

import { _t } from '@web/core/l10n/translation';
import { jsonrpc } from "@web/core/network/rpc_service";
import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({

    /**
     * SPEC-001 §3.4.3 — Sin cambios.
     * Fuerza el flujo a "direct" para ATIX, independientemente del valor original de `flow`.
     */
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== "atix") {
            return this._super(...arguments);
        }
        return this._super(providerCode, paymentOptionId, paymentMethodCode, "direct");
    },

    /**
     * SPEC-001 §3.4.2 — Nuevo flujo server-side.
     *
     * Ya no se carga el SDK de ATIX ni se llama directamente a GBCPE_AuthenticateUser.
     * El backend se encarga de la autenticación y retorna únicamente la URL de redirección.
     *
     * Flujo:
     *   1. Llamar a /payment/atix/authenticate con tx_id
     *   2. Si hay redirect_url → redirigir al navegador
     *   3. Si hay error → mostrar mensaje al usuario
     */
    _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== "atix") {
            return this._super(...arguments);
        }

        return jsonrpc("/payment/atix/authenticate", { tx_id: processingValues.tx_id })
            .then((result) => {
                if (result && result.redirect_url) {
                    window.location.href = result.redirect_url;
                } else {
                    const errorMsg = (result && result.error)
                        || _t("Error al procesar el pago con ATIX.");
                    this._displayErrorDialog(
                        _t("Error de Pago"),
                        errorMsg
                    );
                }
            })
            .catch(() => {
                this._displayErrorDialog(
                    _t("Error de Pago"),
                    _t("No se pudo conectar con la pasarela de pago. Intente nuevamente.")
                );
            });
    },

});