import os
import requests
from bs4 import BeautifulSoup
import uuid
import boto3

def lambda_handler(event, context):
    api_key = os.environ.get("API_KEY")

    if not api_key:
        return {
            'statusCode': 500,
            'body': "La clave de API no está configurada en las variables de entorno"
        }

    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"
    scraperapi_url = f"https://api.scraperapi.com/?api_key={api_key}&url={url}&render=true"

    try:
        response = requests.get(scraperapi_url)
        if response.status_code != 200:
            return {
                'statusCode': response.status_code,
                'body': f"Error al obtener la página: {response.text}"
            }
        html = response.text
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error al acceder a la página web: {str(e)}"
        }

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    headers = [header.text.strip() for header in table.find_all('th')[:-1]]
    rows = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')[:-1]
        rows.append({headers[i]: cell.text.strip() for i, cell in enumerate(cells)})

    dynamodb = boto3.resource('dynamodb')
    dynamodb_table = dynamodb.Table('TablaWebScrappingSismos')

    scan = dynamodb_table.scan()
    with dynamodb_table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4())
        dynamodb_table.put_item(Item=row)
        i += 1

    return {
        'statusCode': 200,
        'body': rows
    }
