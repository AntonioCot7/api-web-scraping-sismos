import json
import os
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Configuración para AWS DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('TABLE_NAME')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Configuración del navegador de Selenium
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Inicializa el driver de Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # URL de la página web que se quiere scrape
    url = "https://ultimosismo.igp.gob.pe/"  # Ajusta la URL según sea necesario
    driver.get(url)

    # Esperar que se cargue la tabla y extraer los datos
    try:
        table_element = driver.find_element(By.CLASS_NAME, "table-responsive")
        rows = table_element.find_elements(By.TAG_NAME, "tr")
        
        data = []
        for row in rows[1:]:  # Ignora el encabezado
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) > 0:
                item = {
                    "id": columns[0].text,
                    "referencia": columns[1].text,
                    "fecha_hora": columns[2].text,
                    "magnitud": columns[3].text,
                    "reporte": columns[4].text
                }
                data.append(item)
                # Guardar cada item en DynamoDB
                table.put_item(Item=item)
        
        driver.quit()
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Datos scrapeados y guardados en DynamoDB", "data": data})
        }
    except Exception as e:
        driver.quit()
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error al hacer scraping o guardar en DynamoDB", "error": str(e)})
        }
