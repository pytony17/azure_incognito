"""
To test locally, run the following in PowerShell:

    $body = @{candidateId = 475} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:7071/api/http_incognito" -Method Post -Body $body -ContentType "application/json"
    $response

"""

import json
import logging
import os
import sys

import azure.functions as func
# Import the parse_postmeta and create_resume modules
from parse_postmeta import get_candidate_data
from create_resume import generate_resume

sys.path.insert(0, os.path.dirname(__file__))

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


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
        try:
            # Call the parse_postmeta function and pass the candidate_id
            resume_data = get_candidate_data(candidate_id)
            logging.info(f"Resume json: {resume_data}")

            # Call the create_resume function to generate the resume document
            resume_document = generate_resume(resume_data)
            logging.info(f"Resume text: {resume_document}")

            response = {
                "version": 'Python %s\n' % sys.version.split()[0],
                "output": resume_document,
                "message": "Resume successfully created."
            }
        except Exception as e:
            logging.error(f"Error in parse_postmeta: {e}")
            response = {
                "version": 'Python %s\n' % sys.version.split()[0],
                "output": None,
                # Update message to reflect the actual error
                "message": f"Error: {e}",
            }
    else:
        logging.error("Missing 'candidateId' in request body")
        return func.HttpResponse("Missing 'candidateId' in request body", status_code=400)

    json_response = json.dumps(response)

    return func.HttpResponse(
        json_response,
        status_code=200,
        mimetype="application/json"
    )
