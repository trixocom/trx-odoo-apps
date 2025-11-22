#!/bin/bash

# Script de instalación automática del módulo pos_create_so
# Autor: Trixocom
# Versión: 18.0.1.0.2

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Instalador pos_create_so v18.0.1.0.2${NC}"
echo -e "${GREEN}  Trixocom - www.trixocom.com${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "__manifest__.py" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse desde el directorio del módulo${NC}"
    echo -e "${YELLOW}Ubicación esperada: /Users/hector/claudecode/odoo18-dev/addons/pos_create_so${NC}"
    exit 1
fi

echo -e "${YELLOW}Paso 1/4: Verificando estructura del módulo...${NC}"
REQUIRED_FILES=(
    "__init__.py"
    "__manifest__.py"
    "models/__init__.py"
    "models/pos_order.py"
    "views/pos_config_views.xml"
    "static/src/app/screens/payment_screen/payment_screen.js"
    "static/src/app/screens/payment_screen/payment_screen.xml"
    "static/src/css/payment_screen.css"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Falta el archivo $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Estructura verificada${NC}"
echo ""

echo -e "${YELLOW}Paso 2/4: Verificando Docker Compose...${NC}"
cd ../../../
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: No se encuentra docker-compose.yml en el directorio raíz${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose encontrado${NC}"
echo ""

echo -e "${YELLOW}Paso 3/4: Reiniciando contenedor Odoo...${NC}"
docker-compose restart web
echo -e "${GREEN}✓ Contenedor reiniciado${NC}"
echo ""

echo -e "${YELLOW}Paso 4/4: Esperando que Odoo esté listo...${NC}"
sleep 10

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Instalación completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo ""
echo "1. Acceder a Odoo: ${GREEN}http://localhost:8069${NC}"
echo "2. Ir a: ${GREEN}Aplicaciones${NC}"
echo "3. Clic en: ${GREEN}Actualizar lista de aplicaciones${NC}"
echo "4. Buscar: ${GREEN}POS - Crear Orden de Venta${NC}"
echo "5. Clic en: ${GREEN}Instalar${NC}"
echo ""
echo -e "${YELLOW}Para verificar funcionamiento:${NC}"
echo "1. Abrir sesión POS"
echo "2. Agregar productos"
echo "3. Seleccionar cliente"
echo "4. Ir a pantalla de pago"
echo "5. Verificar botón verde 'Crear Orden de Venta'"
echo ""
echo -e "${YELLOW}Logs del contenedor:${NC}"
echo "docker-compose logs -f web"
echo ""
echo -e "${GREEN}Documentación completa: README.md${NC}"
echo -e "${GREEN}Guía de instalación: INSTALL.md${NC}"
echo ""
