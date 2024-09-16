/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { Component } from '@odoo/owl';
import { jsonrpc } from "@web/core/network/rpc_service";
import PaymentForm from '@payment/js/payment_form';

const loadScript = (src) => new Promise((resolve, reject) => {
    let script = document.createElement('script')
    script.src = src
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })

PaymentForm.include({
    _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        var self = this;
            if (providerCode != "atix"){
                return this._super(...arguments)
            }
            console.log(processingValues)

            loadScript("https://gateway.atix.com.pe/cdn/gbcpepaymentjs/V1.1/ATIXPaymentGateway.min.js")
            .then(()=>{
                console.log(processingValues)
                $.fn.GBCPE_PaymentGateway.setup.Apikey = processingValues.atix_apikey;
                $.fn.GBCPE_PaymentGateway.setup.Email = processingValues.partner_email //valor opcional;
                $.fn.GBCPE_PaymentGateway.setup.Currency = processingValues.currency_name;
                $.fn.GBCPE_PaymentGateway.setup.Totalamount = processingValues.amount;
                $.fn.GBCPE_PaymentGateway.setup.Reference = processingValues.reference;

                    $.fn.GBCPE_PaymentGateway(function (Result) {
                        var error = Result[0].Error;
                        var Url = Result[0].Url;
                        var Token = Result[0].Token;
                        if (error){
                            alert(error)
                        }else{
                            jsonrpc("/payment/atix/update_token",
                                {tx_id:processingValues.tx_id,token:Token}
                            ).then((res)=>{
                                if(res){
                                    window.location.href = Url;
                                }else{
                                    alert("Error")
                                }
                            }) 
                        }
                    })
                
            })
    },
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
            if (providerCode != "atix"){
                return this._super(...arguments)
            }else{
                return this._super(providerCode, paymentOptionId, paymentMethodCode,"direct")
            }
        }
});