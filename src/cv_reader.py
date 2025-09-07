import os
import glob
from typing import List, Dict, Any, Optional
from docx import Document
import logging

class CVReaderAgent:
    """
    Agente para leer y procesar CVs desde diferentes formatos de archivo.
    
    Funcionalidades principales:
    - Lectura de archivos Word (.docx)
    - Lectura de archivos de texto (.txt)
    - Búsqueda automática de CVs en carpeta especificada
    - Extracción de texto para análisis posterior
    
    Nota: Los formatos .pdf y .doc están declarados pero no implementados.
    """
    
    def __init__(self, cv_folder: str = "curriculums"):
        """
        Inicializa el lector de CVs.
        
        Args:
            cv_folder: Ruta de la carpeta donde se encuentran los CVs
        """
        self.cv_folder = cv_folder
        # Solo extensiones realmente implementadas
        self.supported_extensions = ['.docx', '.txt']
        # Extensiones declaradas pero no implementadas (para futuras mejoras)
        self.unsupported_extensions = ['.pdf', '.doc']
        
    def read_word_document(self, file_path: str) -> str:
        """
        Lee un archivo Word (.docx) y extrae el texto.
        
        Args:
            file_path: Ruta completa al archivo .docx
            
        Returns:
            str: Texto extraído del documento, o string vacío si hay error
        """
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text.strip())
            return '\n'.join(text)
        except Exception as e:
            logging.error(f"Error leyendo archivo Word {file_path}: {str(e)}")
            return ""
    
    def read_text_file(self, file_path: str) -> str:
        """
        Lee un archivo de texto plano.
        
        Args:
            file_path: Ruta completa al archivo .txt
            
        Returns:
            str: Contenido del archivo, o string vacío si hay error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logging.error(f"Error leyendo archivo de texto {file_path}: {str(e)}")
            return ""
    
    def get_cv_files(self) -> List[str]:
        """
        Obtiene la lista de archivos de CV en la carpeta especificada.
        
        Returns:
            List[str]: Lista ordenada de rutas de archivos CV encontrados
        """
        cv_files = []
        
        if not os.path.exists(self.cv_folder):
            logging.warning(f"La carpeta {self.cv_folder} no existe")
            return cv_files
        
        # Buscar archivos con extensiones soportadas
        for ext in self.supported_extensions:
            pattern = os.path.join(self.cv_folder, f"*{ext}")
            cv_files.extend(glob.glob(pattern))
        
        return sorted(cv_files)
    
    def read_cv_file(self, file_path: str) -> Dict[str, Any]:
        """
        Lee un archivo de CV y retorna información estructurada.
        
        Args:
            file_path: Ruta completa al archivo CV
            
        Returns:
            Dict[str, Any]: Diccionario con información del archivo y texto extraído
        """
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extraer texto según el tipo de archivo
        if file_ext == '.docx':
            text = self.read_word_document(file_path)
        elif file_ext == '.txt':
            text = self.read_text_file(file_path)
        else:
            logging.warning(f"Formato de archivo no soportado: {file_ext}")
            text = ""
        
        return {
            'file_name': file_name,
            'file_path': file_path,
            'text': text,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
    
    def read_all_cvs(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        Lee todos los CVs en la carpeta especificada.
        
        Args:
            verbose: Si True, muestra información de progreso en consola
            
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de cada CV
        """
        cv_files = self.get_cv_files()
        cvs = []
        
        if verbose:
            print(f"📁 Buscando CVs en la carpeta: {self.cv_folder}")
            print(f"📄 Archivos encontrados: {len(cv_files)}")
        
        for file_path in cv_files:
            if verbose:
                print(f"  📖 Leyendo: {os.path.basename(file_path)}")
            
            cv_data = self.read_cv_file(file_path)
            if cv_data['text']:
                cvs.append(cv_data)
                if verbose:
                    print(f"    ✅ Extraído: {len(cv_data['text'])} caracteres")
            else:
                if verbose:
                    print(f"    ❌ Error al leer el archivo")
        
        return cvs
    
    def get_cv_texts(self, verbose: bool = False) -> List[str]:
        """
        Obtiene solo los textos de los CVs (método de conveniencia).
        
        Args:
            verbose: Si True, muestra información de progreso
            
        Returns:
            List[str]: Lista de textos extraídos de los CVs
        """
        cvs = self.read_all_cvs(verbose=verbose)
        return [cv['text'] for cv in cvs if cv['text']]
    
    def validate_cv_file(self, file_path: str) -> bool:
        """
        Valida si un archivo es un CV válido y legible.
        
        Args:
            file_path: Ruta al archivo a validar
            
        Returns:
            bool: True si el archivo es válido, False en caso contrario
        """
        if not os.path.exists(file_path):
            return False
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_extensions:
            return False
        
        # Intentar leer el archivo para verificar que no esté corrupto
        try:
            if file_ext == '.docx':
                doc = Document(file_path)
                # Verificar que tenga al menos un párrafo con contenido
                return any(paragraph.text.strip() for paragraph in doc.paragraphs)
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read(100)  # Leer solo los primeros 100 caracteres
                    return len(content.strip()) > 0
        except Exception:
            return False
        
        return False
    
    def get_cv_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de los CVs disponibles en la carpeta.
        
        Returns:
            Dict[str, Any]: Resumen con estadísticas de los CVs
        """
        cv_files = self.get_cv_files()
        valid_files = [f for f in cv_files if self.validate_cv_file(f)]
        
        return {
            'total_files': len(cv_files),
            'valid_files': len(valid_files),
            'supported_formats': self.supported_extensions,
            'unsupported_formats': self.unsupported_extensions,
            'folder_path': self.cv_folder
        }