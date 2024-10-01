{
    "name":"Proveedor de pago: ATIX",
    'category': 'Accounting/Payment Providers',
    "depends":[
        "base_automation",
        "payment",
        "website",

    ],
    "author":"ATIX",
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    "data":[
        "views/template_payment_form.xml",
        "views/payment_provider.xml",
        "views/payment_transaction.xml",
        #"data/payment_method_data.xml",
        "data/payment_provider_data.xml",
        "data/action_server.xml",
        "data/ir_cron.xml",
    ],
    "assets":{
        "web.assets_frontend":[
            "payment_atix/static/src/js/payment_form.js"
        ]
    }
}