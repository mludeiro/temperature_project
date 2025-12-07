from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import os
from datetime import datetime
import uvicorn

# Usar importación absoluta en lugar de relativa
import sys
sys.path.append('/app')
from app.config import DATA_DIR

app = FastAPI(title="Temperature CSV Upload Service")

# Configuración - usar el mismo directorio que el proceso ETL
UPLOAD_DIR = DATA_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home():
    """Página principal simple para subir archivos"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSV File Upload</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; text-align: center; }
            .upload-area { border: 2px dashed #ccc; padding: 30px; text-align: center; margin: 20px 0; }
            .upload-area:hover { border-color: #007bff; }
            input[type="file"] { margin: 10px 0; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #0056b3; }
            .result { margin: 20px 0; padding: 10px; border-radius: 4px; text-align: center; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>📁 CSV File Upload</h1>
        
        <div class="upload-area">
            <form id="uploadForm" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".csv" required>
                <br><br>
                <button type="submit">Upload CSV</button>
            </form>
        </div>
        
        <div id="result"></div>
        
        <script>
            // Función para verificar el estado de la tarea ETL
            async function checkStatus(taskId) {
                const statusDiv = document.getElementById(`status-${taskId}`);
                statusDiv.innerHTML = 'Checking status...';
                
                try {
                    const response = await fetch(`/etl/status/${taskId}`);
                    const data = await response.json();
                    
                    let statusHtml = `<div style="margin-top: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                        <strong>Status:</strong> ${data.status}<br>`;
                    
                    if (data.result) {
                        statusHtml += `<strong>Result:</strong> ${data.result}<br>`;
                    }
                    
                    if (data.error) {
                        statusHtml += `<strong>Error:</strong> ${data.error}<br>`;
                    }
                    
                    statusHtml += `<p><small>Last checked: ${new Date().toLocaleTimeString()}</small></p>`;
                    
                    if (data.status !== 'SUCCESS' && data.status !== 'FAILURE') {
                        statusHtml += `<button onclick="checkStatus('${taskId}')">Refresh Status</button>`;
                    }
                    
                    statusHtml += '</div>';
                    statusDiv.innerHTML = statusHtml;
                    
                } catch (error) {
                    statusDiv.innerHTML = `<div style="color: red;">Error checking status: ${error.message}</div>`;
                }
            }
            
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const resultDiv = document.getElementById('result');
                
                if (!fileInput.files[0]) {
                    resultDiv.innerHTML = '<div class="result error">Please select a CSV file</div>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                resultDiv.innerHTML = '<div class="result">Uploading... ⏳</div>';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <div class="result success">
                                ✅ File uploaded successfully!<br>
                                <strong>Filename:</strong> ${data.filename}<br>
                                <strong>Size:</strong> ${data.size} bytes<br>
                                <strong>ETL Status:</strong> ${data.etl_status}<br>
                                <strong>Task ID:</strong> ${data.task_id}<br>
                                <p>You can check the ETL status <a href="/etl/status/${data.task_id}" target="_blank">here</a>.</p>
                                <button onclick="checkStatus('${data.task_id}')">Check Status</button>
                                <div id="status-${data.task_id}"></div>
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<div class="result error">❌ Error: ${data.detail}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="result error">❌ Network error: ${error.message}</div>`;
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint para subir archivos CSV"""
    
    # Validar que sea un archivo CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Preparar para enviar el archivo a la API principal
        import aiohttp
        from io import BytesIO
        
        # Leer el contenido del archivo
        content = await file.read()
        file_size = len(content)
        
        # Crear un objeto FormData para enviar el archivo
        data = aiohttp.FormData()
        data.add_field('file',
                      BytesIO(content),
                      filename=file.filename,
                      content_type='text/csv')
        
        # Enviar el archivo a la API principal
        async with aiohttp.ClientSession() as session:
            async with session.post('http://fastapi_app:8000/datasets', data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Devolver respuesta con información del proceso ETL
                    return {
                        "message": "File uploaded successfully and ETL process started",
                        "filename": file.filename,
                        "size": file_size,
                        "etl_status": result["status"],
                        "task_id": result["task_id"],
                        "status_url": f"/etl/status/{result['task_id']}"
                    }
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"API Error: {error_text}")
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@app.get("/files")
async def list_files():
    """Listar todos los archivos subidos"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith('.csv'):
                filepath = os.path.join(UPLOAD_DIR, filename)
                file_size = os.path.getsize(filepath)
                files.append({
                    "filename": filename,
                    "size": file_size
                })
        
        return {"files": files, "total": len(files)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@app.get("/etl/status/{task_id}")
async def check_etl_status(task_id: str):
    """Verificar el estado de una tarea ETL"""
    try:
        import aiohttp
        
        # Consultar el estado de la tarea en la API principal
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://fastapi_app:8000/etl/status/{task_id}') as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"API Error: {error_text}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Simple Upload Service on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)