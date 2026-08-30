# Trixocom - Geo-barrera de Asistencias (`trx_attendance_geofence`)

Bloquea el ingreso/egreso de asistencias (Odoo 19, Community) si el empleado
no está físicamente en la ubicación de trabajo que le corresponde.

## Qué hace

- Agrega **latitud, longitud y radio de tolerancia (m)** a las Ubicaciones de
  trabajo (`hr.work.location`), con botón "Ver en el mapa" para verificar el
  punto en Google Maps.
- Al fichar desde el **systray** (navegador de PC o celular) valida en el
  **servidor** (fórmula de Haversine) que las coordenadas del empleado estén
  dentro del radio de su ubicación asignada. Fuera del radio → el fichaje se
  rechaza con el detalle de la distancia.
- **Sin GPS no se ficha**: si el empleado niega el permiso de ubicación o no
  hay señal, el fichaje se bloquea (se reemplaza el "Continuar de todos
  modos" estándar de Odoo). La validación es server-side: no se saltea
  deshabilitando JavaScript.
- **hr_homeworking**: si está instalado, se valida contra la ubicación del
  día: excepción de hoy → ubicación del día de la semana → ubicación del
  contrato (`work_location_id`).
- **Kiosco exento**: el fichaje por kiosco (tablet en el lugar de trabajo) no
  valida geo-barrera. Los registros manuales de RRHH tampoco.
- **Exento de geo-barrera** por empleado (ficha del empleado → RRHH →
  pestaña de organización), para supervisores o personal móvil.

## Configuración

1. Instalar el módulo (activa solo el "Seguimiento de dispositivo y
   ubicación" de Asistencias en todas las compañías; no toca nada más).
2. Empleados → Configuración → Ubicaciones de trabajo: en cada ubicación,
   activar "Geo-barrera activa" y cargar latitud/longitud (de Google Maps:
   clic derecho sobre el punto → copiar coordenadas) y el radio en metros
   (100 m por defecto).
3. Asignar a cada empleado su Ubicación de trabajo (ficha del empleado,
   pestaña Información de trabajo).
4. Los empleados que pueden fichar desde cualquier lado: marcar "Exento de
   geo-barrera".

Una ubicación **sin** geo-barrera activa no restringe nada: los empleados
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
