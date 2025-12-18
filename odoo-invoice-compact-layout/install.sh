#!/bin/bash
################################################################################
# Script de Instalación Automática - Invoice Compact Layout para Odoo 18
# Versión: 1.0.0
# Autor: TrixoCom
################################################################################

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Banner
echo "=============================================="
echo " Invoice Compact Layout - Instalador Odoo 18"
echo "=============================================="
echo ""

# 1. Detectar si es instalación Docker o manual
print_message "Detectando tipo de instalación..."

if command -v docker &> /dev/null; then
    print_message "Docker detectado!"
    INSTALL_TYPE="docker"
elif systemctl list-units --type=service | grep -q odoo; then
    print_message "Instalación manual de Odoo detectada!"
    INSTALL_TYPE="manual"
else
    print_error "No se pudo detectar Odoo. Asegúrate de que Odoo 18 esté instalado."
    exit 1
fi

# 2. Solicitar ruta de addons
echo ""
print_message "Ingresa la ruta donde se instalarán los addons personalizados:"
print_warning "Ejemplo Docker: /opt/odoo/extra-addons"
print_warning "Ejemplo Manual: /opt/odoo/addons"
read -p "Ruta: " ADDONS_PATH

# Validar que la ruta existe
if [ ! -d "$ADDONS_PATH" ]; then
    print_error "La ruta $ADDONS_PATH no existe."
    read -p "¿Deseas crearla? (s/n): " CREATE_PATH
    if [ "$CREATE_PATH" = "s" ] || [ "$CREATE_PATH" = "S" ]; then
        sudo mkdir -p "$ADDONS_PATH"
        print_message "Ruta creada: $ADDONS_PATH"
    else
        print_error "Instalación cancelada."
        exit 1
    fi
fi

# 3. Clonar repositorio
print_message "Clonando repositorio desde GitHub..."
cd "$ADDONS_PATH"

if [ -d "odoo_invoice_compact" ]; then
    print_warning "El directorio odoo_invoice_compact ya existe."
    read -p "¿Deseas sobrescribirlo? (s/n): " OVERWRITE
    if [ "$OVERWRITE" = "s" ] || [ "$OVERWRITE" = "S" ]; then
        sudo rm -rf odoo_invoice_compact
    else
        print_error "Instalación cancelada."
        exit 1
    fi
fi

sudo git clone https://github.com/trixocom/odoo-invoice-compact-layout.git odoo_invoice_compact

if [ $? -ne 0 ]; then
    print_error "Error al clonar el repositorio."
    exit 1
fi

print_message "Repositorio clonado exitosamente!"

# 4. Establecer permisos
print_message "Estableciendo permisos..."

if [ "$INSTALL_TYPE" = "docker" ]; then
    sudo chown -R 101:101 odoo_invoice_compact/  # Usuario odoo en Docker
elif [ "$INSTALL_TYPE" = "manual" ]; then
    sudo chown -R odoo:odoo odoo_invoice_compact/
fi

sudo chmod -R 755 odoo_invoice_compact/

print_message "Permisos establecidos correctamente!"

# 5. Reiniciar Odoo
print_message "Reiniciando Odoo..."

if [ "$INSTALL_TYPE" = "docker" ]; then
    print_message "Detectando contenedor de Odoo..."
    
    # Intentar con docker-compose
    if [ -f "docker-compose.yml" ] || [ -f "../docker-compose.yml" ]; then
        print_message "Reiniciando con docker-compose..."
        docker-compose restart odoo 2>/dev/null || docker compose restart odoo
    else
        # Intentar con docker directamente
        ODOO_CONTAINER=$(docker ps --filter "name=odoo" --format "{{.Names}}" | head -1)
        if [ -z "$ODOO_CONTAINER" ]; then
            print_warning "No se pudo detectar el contenedor de Odoo."
            print_warning "Por favor, reinicia manualmente el contenedor."
        else
            docker restart "$ODOO_CONTAINER"
            print_message "Contenedor $ODOO_CONTAINER reiniciado!"
        fi
    fi
elif [ "$INSTALL_TYPE" = "manual" ]; then
    sudo systemctl restart odoo
    print_message "Servicio Odoo reiniciado!"
fi

# 6. Instrucciones finales
echo ""
echo "=============================================="
print_message "¡Instalación completada exitosamente!"
echo "=============================================="
echo ""
print_message "Próximos pasos:"
echo ""
echo "1. Inicia sesión en Odoo como administrador"
echo "2. Ve a Configuración → Activar el modo desarrollador"
echo "3. Ve a Aplicaciones → Actualizar Lista de Aplicaciones"
echo "4. Busca 'Invoice Compact Layout' y haz click en Instalar"
echo "5. Imprime una factura para verificar el nuevo espaciado"
echo ""
print_message "Ruta de instalación: $ADDONS_PATH/odoo_invoice_compact"
echo ""
print_warning "IMPORTANTE: Si el módulo no aparece, verifica que la ruta"
print_warning "$ADDONS_PATH esté incluida en el archivo de configuración de Odoo"
echo ""
print_message "Documentación: https://github.com/trixocom/odoo-invoice-compact-layout"
echo ""

# Log de instalación
LOG_FILE="/tmp/odoo_invoice_compact_install.log"
echo "Instalación completada el $(date)" > "$LOG_FILE"
echo "Ruta: $ADDONS_PATH/odoo_invoice_compact" >> "$LOG_FILE"
echo "Tipo: $INSTALL_TYPE" >> "$LOG_FILE"

print_message "Log guardado en: $LOG_FILE"
echo ""
