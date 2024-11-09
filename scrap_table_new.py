from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import boto3
import uuid
import time

def lambda_handler(event, context):
    # Configurar las opciones del navegador para modo sin cabeza
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Iniciar el navegador de Selenium
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # URL de la página web que contiene la tabla de sismos
        url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
        driver.get(url)
        
        # Esperar unos segundos para que el JavaScript cargue el contenido
        time.sleep(5)  # Ajusta el tiempo según sea necesario

        # Buscar la tabla por clase o ID (ajusta el selector según corresponda)
        table = driver.find_element(By.CSS_SELECTOR, 'table.table-hover')
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        # Obtener los encabezados de la tabla
        headers = [header.text.strip() for header in rows[0].find_elements(By.TAG_NAME, "th")]

        # Extraer las filas de datos de la tabla
        data_rows = []
        for row in rows[1:11]:  # Limitar a las 10 filas más recientes
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == len(headers):
                data = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
                data_rows.append(data)

        # Guardar los datos en DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('TablaWebScrapping_New')

        # Eliminar todos los elementos de la tabla antes de agregar los nuevos
        scan = table.scan()
        with table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'id': each['id']
                    }
                )

        # Insertar los nuevos datos
        for row in data_rows:
            row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
            table.put_item(Item=row)

        return {
            'statusCode': 200,
            'body': data_rows
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
    
    finally:
        # Cerrar el navegador
        driver.quit()
