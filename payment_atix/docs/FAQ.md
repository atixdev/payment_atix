# Proveedor de Pago: ATIX — Preguntas Frecuentes

## General

### ¿Qué hace este módulo?
Permite que los clientes de tu tienda en línea paguen sus pedidos usando la pasarela de pago **ATIX** de Global Bridge Connections. Al elegir ATIX en el checkout, el cliente es redirigido al portal de pago seguro de ATIX donde ingresa los datos de su tarjeta.

### ¿En qué monedas puedo cobrar?
El módulo soporta pagos en **Soles peruanos (PEN)** y **Dólares americanos (USD)**.

### ¿Necesito instalar algo adicional en Odoo?
No, solo necesitas instalar este módulo. Los módulos de **Sitio Web**, **eCommerce** y **Contabilidad** deben estar activos (son dependencias incluidas automáticamente).

### ¿Necesito un contrato con ATIX?
Sí. Debes tener contrato con **Global Bridge Connections** y obtener las **API KEYs** para soles y dólares. Contacta a GBC directamente para obtener tus credenciales.

---

## Configuración

### ¿Cómo configuro mis credenciales de ATIX?
1. Ve a **Sitio Web > Configuración > Proveedores de pago**
2. Busca y abre el proveedor **ATIX**
3. Ingresa tu **API KEY (PEN)** en el campo de soles
4. Ingresa tu **API KEY (USD)** en el campo de dólares
5. Copia el valor del campo **URL Status** y regístralo en tu panel de administración de ATIX como "Return URL"
6. Guarda los cambios

### ¿Qué es la "URL Status" y para qué sirve?
Es una dirección web generada automáticamente por Odoo. ATIX la usa para notificar a tu sistema cuando un pago ha sido procesado. Debes registrarla en el panel de ATIX, en el campo "Return URL".

### ¿Puedo usar ATIX solo para soles y no para dólares?
Sí. Si solo tienes API KEY para soles, deja el campo de USD vacío. El sistema solo procesará pagos en soles.

---

## Uso Diario

### ¿Cómo paga un cliente con ATIX?
1. El cliente agrega productos al carrito y va al checkout
2. Selecciona **ATIX** como método de pago
3. Al confirmar, es redirigido de forma segura a la página de pago de ATIX
4. El cliente ingresa los datos de su tarjeta en el portal de ATIX
5. Una vez aprobado, el pedido queda confirmado automáticamente y el cliente regresa a la tienda

### ¿Cómo sé si un pago fue aprobado?
Ve a **Contabilidad > Clientes > Transacciones de pago** y filtra por **ATIX**. Las transacciones aprobadas aparecen en estado **Completado** y tienen un **Código de Referencia** asignado.

### ¿Cada cuánto tiempo se actualiza el estado de los pagos?
El sistema consulta automáticamente el estado de los pagos pendientes **cada 2 minutos**. Las transacciones más antiguas de 6 horas no se consultan automáticamente.

### ¿Puedo verificar el estado de un pago manualmente?
Sí:
1. Ve a **Contabilidad > Clientes > Transacciones de pago**
2. Abre la transacción que quieres verificar
3. Haz clic en **Acción > Consulta estado de pago por pasarela ATIX**

---

## Problemas Comunes

### El cliente ve un error al intentar ir al pago

**Causa**: La API KEY configurada es incorrecta, la moneda del pedido no tiene API KEY asignada, o hay un problema de conectividad con ATIX al generar la sesión de pago.

**Solución**:
1. Verifica que la API KEY para la moneda del pedido (PEN o USD) esté correctamente configurada en el proveedor
2. Confirma con GBC que tu API KEY está activa
3. Verifica que el servidor Odoo tenga acceso a internet hacia `gateway.atix.com.pe`

### La transacción queda en estado "Pendiente" indefinidamente

**Causa**: El cliente abandonó el portal de ATIX sin completar el pago, o hubo un error de conectividad al consultar el estado tras el retorno del cliente.

**Solución**:
1. Ve a la transacción y ejecuta **Acción > Consulta estado de pago por pasarela ATIX** para forzar una consulta inmediata
2. Si ya han pasado más de 6 horas, el cron no la revisará; debes verificarla manualmente en el panel de ATIX

### El cliente completó el pago pero el pedido sigue pendiente

**Causa**: El cron aún no ha ejecutado la consulta de estado, o la respuesta de ATIX no llegó todavía.

**Solución**:
1. Espera hasta 2 minutos para que el cron actualice el estado
2. Si persiste, ejecuta la consulta manual desde el formulario de la transacción

### No aparece ATIX como método de pago en el checkout

**Causa**: El proveedor ATIX no está habilitado o no está publicado en el sitio web.

**Solución**:
1. Ve a **Sitio Web > Configuración > Proveedores de pago**
2. Verifica que ATIX esté en estado **Habilitado** y publicado
3. Asegúrate de que las monedas configuradas coincidan con las del pedido

---

## Consejos y Trucos

- **Prueba en staging primero**: Antes de activar en producción, verifica el flujo completo con un pedido de prueba.
- **Guarda ambas API Keys**: Aunque solo uses una moneda, configura ambas claves para evitar errores si en el futuro se hacen pedidos en otra moneda.
- **Monitorea las transacciones pendientes**: Revisa periódicamente las transacciones en estado "Pendiente" con más de 6 horas para gestionarlas manualmente.
- **La URL Status es única**: Si cambias el dominio de tu tienda, deberás actualizar la URL en el panel de ATIX.
- **Actualizaciones seguras**: Gracias a la protección del módulo (`noupdate="1"`), puedes actualizar la aplicación (`-u payment_atix`) sin miedo a perder tus claves API configuradas en producción.
