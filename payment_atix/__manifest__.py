{
    "name":"Proveedor de pago: ATIX",
    'category': 'Accounting/Payment Providers',
    "summary": 'Integración con la pasarela de pago Atix',
    'description': """
        Este módulo permite la integración de Odoo con la pasarela de pago Atix, facilitando la gestión de pagos en línea de manera segura y eficiente.

        Requisitos:
        - Instancia de Odoo Community o Enterprise
        - Alojamiento “on premise” (Local, en la nube) u “odoo.sh”
        - Tener la aplicación "Proveedor de pago: ATIX" dentro de la lista de aplicaciones del sistema
        - API KEY (Soles y/o dólares) de comercio Global Bridge Connections

    """,
    "depends":[
        "payment",
        "base_automation",
        "website",
        "website_sale"
    ],
    'images': ['static/description/banner.png'],
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