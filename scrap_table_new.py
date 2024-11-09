import json
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Inicializar DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TableWebScrapping_New')

def lambda_handler(event, context):
    # Configuración del navegador sin interfaz
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Inicializar el navegador
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navegar a la URL
        url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
        driver.get(url)
        
        # Esperar a que la tabla se cargue
        driver.implicitly_wait(10)
        
        # Extraer los datos de la tabla de sismos
        rows = driver.find_elements(By.CSS_SELECTOR, "app-table tbody tr")
        data_to_save = []

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 4:
                reporte = columns[0].text
                referencia = columns[1].text
                fecha_hora = columns[2].text
                magnitud = columns[3].text
                
                # Crear un diccionario con los datos
                item = {
                    "id": reporte,
                    "referencia": referencia,
                    "fecha_hora": fecha_hora,
                    "magnitud": magnitud
                }
                
                # Guardar en la tabla de DynamoDB
                table.put_item(Item=item)
                data_to_save.append(item)
        
        # Cerrar el navegador
        driver.quit()

        # Respuesta
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Datos guardados en DynamoDB", "data": data_to_save})
        }

    except Exception as e:
        driver.quit()
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }
