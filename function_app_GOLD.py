"""
To test locally, run the following in PowerShell:

    $body = @{candidateId = 888} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:7071/api/http_incognito" -Method Post -Body $body -ContentType "application/json"
    $response

"""
import mysql.connector
import azure.functions as func
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

user = "shoregateconsulting"
password = "ShoreG8!"
host = "198.12.217.64"
# host = "98.12.217.64"  # simulate invalid IP (not whitelisted in cPanel)
database = "i9739295_xhhk1"


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            user=user, password=password, host=host, database=database)
        logging.info("Connected to the database successfully!")
        return conn
    except mysql.connector.Error as err:
        logging.error(f'DB connection error: {err}')
        raise err


@app.route(route="http_incognito")
def http_incognito(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Failed to parse request body as JSON")
        return func.HttpResponse("Invalid request body", status_code=400)

    logging.info(f"Received data: {req_body}")

    candidate_id = req_body.get('candidateId')
    if candidate_id:
        # Process the candidate ID
        response = {
            "version": 'Python %s\n' % sys.version.split()[0],
            "output": candidate_id,
            "message": "Resume successfully created."
        }
        logging.info(f"Candidate ID: {candidate_id}")
    else:
        logging.error("Missing 'candidateId' in request body")
        return func.HttpResponse("Missing 'candidateId' in request body", status_code=400)

    # Create a response JSON document
    if candidate_id:
        # Establish a database connection
        try:
            conn = get_db_connection()
            # Close the database connection
            conn.close()
        except mysql.connector.Error as err:
            response.update({
                "output": candidate_id,
                "message": (f'DB connection error: {err}'),
            })
            logging.error(f'DB connection error: {err}')
    else:
        response = {
            "version": 'Python %s\n' % sys.version.split()[0],
            "output": None,
            "message": "No data received. Resume not created.",
        }

    json_response = json.dumps(response)

    return func.HttpResponse(
        json_response,
        status_code=200,
        mimetype="application/json"
    )
