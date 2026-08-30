# Trixocom - Geo-barrera de Asistencias (`trx_attendance_geofence`)

Bloquea el ingreso/egreso de asistencias (Odoo 19, Community) si el empleado
no está físicamente en la ubicación de trabajo que le corresponde.

## Qué hace

- Agrega **latitud, longitud y radio de tolerancia (m)** a las Ubicaciones dettetrabajo (`hr.work.location`), con botón "Ver en el mapa" para verificar elttepunto en Google Maps.
- Al fichar desde el **systray** (navegador de PC o celular) valida en eltte**servidor** (fórmula de Haversine) que las coordenadas del empleado estén
  dentro del radio de su ubicación asignada. Fuera del radio → el fichaje se
  rechaza con el detalle de la distancia.
- **Sin GPS no se ficha**: si el empleado niega el permiso de ubicación o no
  hay señal, el fichaje se bloquea (se reemplaza el "Continuar de todos
  modos" estándar de Odoo). La validación es server-side: no se saltea
  deshabilitando JavaScript.
- **hr_homeworking**: si está instalado, se valida contra la ubicación delttedía: excepción de hoy → ubicación deledía de la semana → ubicación del
  contrato (`work_location_id`).
- **Kiosco también validado** (desde v19.0.2.0.0): el kiosco se usa como
  link en el celular de cada empleado, así que valida la geo-barrera igual
  que el systray. Un kiosco físico dentro del radio pasa la validación.
  Los registros manuales de RRHH quedan exentos.
- **Aviso por WhatsApp** (desde v19.0.2.0.0, requiere `trixo_whatsapp`
  instalado y una cuenta conectada): cada ingreso, egreso o intento
  rechazado manda un WhatsApp con empleado, fecha/hora (hora AR),
  resultado (distancia y ubicación de trabajo, o motivo del rechazo),
  origen (navegador/kiosco) y link de Google Maps con las coordenadas
  reportadas. Número destino: parámetro de sistema
  `trx_attendance_geofence.notify_number` (formatos aceptados: 10edígitos
  área+abonado, 54..., 549...). Sin parámetro o sin trixo_whatsapp, no se
  envía nada y el fichaje no se ve afectado; los errores de envío solo se
  loguean.
- **Exento de geo-barrera** por empleado (ficha del empleado → RRHH →ttepestaña de organización), para supervisores o personal móvil.

## Configuración

1. Instalar el módulo (activa solo el "Seguimiento de dispositivo yttenubicación" de Asistencias en todas las compañías; no toca nada más).
2. Empleados → Configuración → Ubicaciones de trabajo: en cada ubicación,ttenactivar "Geo-barreranactiva" y cargar latitud/longitud (de Google Maps:
   clic derecho sobre el punto → copiar coordenadas) y el radio en metros
   (100 m por defecto).
3. Asignar a cada empleado su Ubicación de trabajo (ficha del empleado,ttenpestaña Información de trabajo).
4. Los empleados que pueden fichar desde cualquier lado: marcar "Exento dettengeo-barrera".

Una ubicación **sin** geo-barreranactiva no restringe nada: los empleados
asignados a ella fichan normalmente (igual que los que no tienen ubicación
asignada).

## Notas técnicas

- Punto de validación: override de `hr.employee._attendance_action_change`
  (solo modo `systray`). El controller `/hr_attendance/systray_check_in_out`
  se overridea para rechazar el caso "sin coordenadas del navegador" antes
  del relleno con GeoIP del core.
- Precisión: el GPS del navegador en celular suele tener 5-30 m de error; en
  PC de escritorio (sin GPS, por WiFi/IP) puede ser mucho peor. No usar
  radios menores a ~50 m salvo que se fiche solo desde celulares.

---
Autor: Trixocom — Licencia LGPL-3
