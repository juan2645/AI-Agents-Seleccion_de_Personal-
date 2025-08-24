# Sistema de Selección de Personal - CVs desde Carpeta

## 📁 Funcionalidad de CVs desde Carpeta

El sistema ahora puede leer CVs directamente desde archivos Word (.docx) y otros formatos en una carpeta.

### 🚀 Cómo usar

#### 1. Preparar la carpeta de CVs
```
Seleccion_de_Personal/
├── curriculums/            # Carpeta para tus CVs
│   ├── candidato1.docx
│   ├── candidato2.docx
│   └── candidato3.docx
├── reportes/               # Carpeta para los reportes generados
│   ├── reporte_resumen.txt
│   ├── reporte_detallado.json
│   └── reporte_reclutamiento_*.xlsx
├── main.py
└── ...
```

#### 2. Colocar tus CVs
- Copia tus archivos de CV (.docx, .doc, .txt) en la carpeta `curriculums/`
- El sistema automáticamente detectará y procesará todos los archivos

#### 3. Ejecutar el sistema

**Opción A: Ejemplo con CVs de la carpeta**
```bash
python main.py example-folder
```

**Opción B: Servidor API**
```bash
python main.py
```
Luego usar el endpoint: `POST /process-recruitment-from-folder`

### 📄 Formatos Soportados

- ✅ **Word (.docx)** - Recomendado
- ✅ **Word (.doc)** - Formato antiguo
- ✅ **Texto (.txt)** - Texto plano
- ⚠️ **PDF (.pdf)** - En desarrollo

### 🔧 Comandos Disponibles

```bash
# Crear CVs de ejemplo en formato Word
python create_sample_cvs.py

# Ejecutar ejemplo con CVs hardcodeados
python main.py example

# Ejecutar ejemplo con CVs desde la carpeta
python main.py example-folder

# Iniciar servidor API
python main.py
```

### 🌐 Endpoints de la API

#### Nuevos endpoints para CVs desde carpeta:

1. **`POST /process-cvs-from-folder`**
   - Lista todos los CVs encontrados en la carpeta
   - Retorna información de cada archivo

2. **`POST /process-recruitment-from-folder`**
   - Procesa un reclutamiento completo usando CVs de la carpeta
   - Acepta un perfil de trabajo opcional

### 📊 Ejemplo de Uso

1. **Crear CVs de ejemplo:**
```bash
python create_sample_cvs.py
```

2. **Procesar reclutamiento:**
```bash
python main.py example-folder
```

3. **Resultado esperado:**
```
📁 Buscando CVs en la carpeta: curriculums
📄 Archivos encontrados: 3
  📖 Leyendo: juan_perez_senior_python.docx
    ✅ Extraído: 626 caracteres
  📖 Leyendo: maria_gonzalez_fullstack.docx
    ✅ Extraído: 628 caracteres
  📖 Leyendo: carlos_rodriguez_data_analyst.docx
    ✅ Extraído: 590 caracteres
```

### 💡 Consejos

1. **Nombres de archivo descriptivos:** Usa nombres que identifiquen al candidato
   - ✅ `juan_perez_desarrollador_python.docx`
   - ❌ `cv1.docx`

2. **Formato Word recomendado:** Los archivos .docx mantienen mejor el formato

3. **Estructura del CV:** Asegúrate de que el CV contenga:
   - Nombre y contacto
   - Experiencia laboral
   - Habilidades técnicas
   - Educación

4. **Carpeta limpia:** Solo archivos de CV en la carpeta `curriculums/`

### 🔍 Solución de Problemas

**Error: "No se encontraron CVs"**
- Verifica que la carpeta `curriculums/` existe
- Asegúrate de que hay archivos con extensiones soportadas
- Ejecuta `python create_sample_cvs.py` para crear ejemplos

**Error: "Formato no soportado"**
- Convierte archivos a formato .docx
- Usa solo extensiones: .docx, .doc, .txt

**Error: "No se pudo leer el archivo"**
- Verifica que el archivo no esté corrupto
- Asegúrate de que el archivo no esté abierto en Word

### 📈 Ventajas

- ✅ **Fácil de usar:** Solo copia archivos a la carpeta
- ✅ **Múltiples formatos:** Soporta Word, texto y más
- ✅ **Procesamiento automático:** Detecta archivos automáticamente
- ✅ **Escalable:** Puede procesar cientos de CVs
- ✅ **API integrada:** Endpoints para integración con otros sistemas
