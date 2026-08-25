#!/bin/bash

# Script de instalación - Stock Packaging Invoice Report
# Autor: Trixocom - www.trixocom.com
# Versión: 18.0.1.0.2

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Stock Packaging Invoice Report v18.0.1.0.2${NC}"
echo -e "${GREEN}  Trixocom - www.trixocom.com${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Verificar ubicación
if [ ! -f "__manifest__.py" ]; then
    echo -e "${RED}Error: Ejecutar desde el directorio del módulo${NC}"
    exit 1
fi

echo -e "${YELLOW}Paso 1/5: Verificando estructura...${NC}"
REQUIRED_FILES=(
    "__init__.py"
    "__manifest__.py"
    "models/__init__.py"
    "models/account_move_line.py"
    "views/account_move_views.xml"
    "report/account_invoice_report.xml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Falta $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ Estructura OK${NC}"

echo -e "${YELLOW}Paso 2/5: Verificando dependencias...${NC}"
cd ../../../

if [ ! -d "addons/stock_packaging_report" ]; then
    echo -e "${RED}Error: Se requiere stock_packaging_report${NC}"
    echo -e "${YELLOW}Instalar primero stock_packaging_report${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dependencias OK${NC}"

echo -e "${YELLOW}Paso 3/5: Verificando Docker...${NC}"
if ! docker-compose ps | grep -q "web"; then
    echo -e "${RED}Error: Contenedor Odoo no está corriendo${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker OK${NC}"

echo -e "${YELLOW}Paso 4/5: Reiniciando Odoo...${NC}"
docker-compose restart web
sleep 10
echo -e "${GREEN}✓ Odoo reiniciado${NC}"

echo -e "${YELLOW}Paso 5/5: Verificando acceso...${NC}"
if curl -s http://localhost:8069 > /dev/null; then
    echo -e "${GREEN}✓ Odoo accesible${NC}"
else
    echo -e "${RED}Warning: No se puede acceder a Odoo${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✓ Instalación completada${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANTE: Instalar stock_packaging_report primero${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Acceder: ${GREEN}http://localhost:8069${NC}"
echo "2. Ir a: ${GREEN}Aplicaciones${NC}"
echo "3. Actualizar lista de aplicaciones"
echo "4. Instalar: ${GREEN}stock_packaging_report${NC} (si no está instalado)"
echo "5. Instalar: ${GREEN}Stock Packaging Invoice Report${NC}"
echo ""
echo -e "${YELLOW}Configuración:${NC}"
echo "1. Inventario → Configuración → Ajustes"
echo "2. Buscar: 'Nombre del Embalaje para Stock'"
echo "3. Configurar: ej. 'Caja', 'Bulto', 'Pallet'"
echo ""
echo -e "${YELLOW}Uso:${NC}"
echo "1. Configurar embalajes en productos"
echo "2. Crear factura con productos"
echo "3. Ver columna 'Cantidad de Embalaje'"
echo ""
echo -e "${GREEN}Documentación: README.md${NC}"
