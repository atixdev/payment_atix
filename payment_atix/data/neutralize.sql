-- disable mercado_pago payment provider
UPDATE payment_provider
   SET atix_apikey_pen = NULL, atix_apikey_usd = NULL;
