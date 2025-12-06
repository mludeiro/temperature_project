from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import os
from datetime import datetime
import uvicorn

app = FastAPI(title="Simple Upload Service")

# Configuración
UPLOAD_DIR = "/app/uploads"
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
                                <strong>Size:</strong> ${data.size} bytes
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
    
    # Generar nombre único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Guardar archivo
    try:
        with open(filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = len(content)
        
        return {
            "message": "File uploaded successfully",
            "filename": filename,
            "size": file_size,
            "path": filepath
        }
        
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


if __name__ == "__main__":
    print("🚀 Starting Simple Upload Service on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)