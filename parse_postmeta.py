"""
For a given candidate in the Incognito Careers database, retrieve the relevant resume records 
(stored in the postmeta table), parse the records to retrieve the information needed to generate
a resume, pass the parsed data in json format to an AI LLM, and get a great resumein text form which is then 
converted to PDF or Word doc format. Store the resume doc and pass a link to it back to the 
Word Press application so the candidate can retrieve it.

Args:
    candidate_id: The value for the current candidate which is used as the post_id to 
    retrieve relevant records from the incognito MySQL database.

Returns:
    Currently, returns a json dump of the candidate's resume info.
    Ultimately, will return a link to a PDF or Word resume document.

"""

import configparser
import datetime
import json
import mysql.connector
import os
import phpserialize
import re


def parse_php_serialized(data):
    """
    Parses a PHP serialized string using the phpserialize package.
    Args:
        data: The PHP serialized string to parse.
    Returns:
        A Python list of values or the original data on error.
    """
    try:
        parsed_data = phpserialize.loads(data.encode('utf-8'))
    except Exception as e:
        print(f"Error parsing data: {e}")
        return data  # Return original data on error

    # Check if parsed data is a dictionary
    if isinstance(parsed_data, dict):
        # Convert dictionary values (bytes) to strings and return as list
        return [value.decode('utf-8') for value in parsed_data.values()]
    else:
        # Not a dictionary, return the original data
        return data


def clean_description(description):
    """
    Cleans the description text by removing HTML tags, special characters, and formatting.
    Args:
        description (str): The description text to be cleaned.
    Returns:
        str: The cleaned description text.
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', description)
    # Remove leading/trailing newlines, carriage returns, whitespace, and special characters
    text = text.strip('\n\r\t\u2019')
    # Remove bullet points and tabs
    text = re.sub(r'^\s*[\u2022\uf0a7]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\t+', '', text, flags=re.MULTILINE)
    # Remove multiple consecutive newlines and carriage returns
    text = re.sub(r'[\n\r]\s*[\n\r]+', '\n', text)
    # Replace remaining newline and carriage return characters with spaces
    text = text.replace('\n', ' ').replace('\r', ' ')
    return text


def clean_date(date_str):
    """
    Cleans the date string by removing the day of the month.
    Args:
        date_str (str): The date string to be cleaned.
    Returns:
        str: The cleaned date string in the format "Month Year".
    """
    try:
        date = datetime.datetime.strptime(date_str, "%B %d %Y")
        return date.strftime("%B %Y")
    except ValueError:
        return ""


def parse_education_records(records):
    """
    Parses a list of education records and converts them to JSON format.

    Args:
        records: A list of dictionaries containing education data.

    Returns:
        A JSON string representing the education data.
    """
    education = []
    count_degrees = None

    # Extract the education data from the records
    for record in records:
        # Extract the education data from the record
        if not count_degrees:
            count_degrees = parse_php_serialized(record.get('meta_value'))
        degree_value = (next
                        ((r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_title'), ""))
        university_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_academy'), "")
        description_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_description'), "")
        start_date_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_start_date'), "")
        end_date_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_end_date'), "")
        # start_date_hidden_value = next(
        #     (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_edu_start_date_hiden'), "")
        # end_date_hidden_value = next(
        #     (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_edu_end_date_hiden'), "")
        is_present_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_education_date_prsnt'), "")

        # Parse the degree, university, and description
        degrees = parse_php_serialized(degree_value)
        start_dates = parse_php_serialized(
            start_date_value) or parse_php_serialized(start_date_hidden_value)
        end_dates = parse_php_serialized(
            end_date_value) or parse_php_serialized(end_date_hidden_value)
        universities = parse_php_serialized(university_value)
        descriptions = parse_php_serialized(description_value)

    # Process each education record
    for i in range(len(count_degrees)):
        degree = degrees[i]
        university = universities[i]
        description = descriptions[i]
        start_date = clean_date(start_dates[i] or start_dates_hidden[i])
        end_date = clean_date(end_dates[i] or end_dates_hidden[i])

        # Combine and format dates if both start and end dates are available
        if start_date and end_date:
            year = f"{start_date} - {end_date}"
        elif start_date and (is_present[i] or is_present[i] == 'on'):
            year = f"{start_date} - Present"
        else:
            year = start_date or end_date or ""

        # Remove HTML tags, special characters and formatting
        text = clean_description(description)

        # Extract the location from the description
        # location = ""
        # if description:
        #     location_match = re.search(r'(?<=, ).*', description)
        #     if location_match:
        #         location = location_match.group()

        # Create the education dictionary
        education_data = {
            "degree": degree,
            "university": university,
            # "location": location,
            "year": year,
            "description": text,
        }
        education.append(education_data)

    # Directly return the list of parsed education records
    return education if education else None


def parse_workhistory_records(records):
    """
    NEEDS TO BE UPDATED TO HANDLE MULTIPLE SETS OF EXPERIENCE RECORDS

    Parses a list of work history records and converts them to JSON format.

    Args:
        records: A list of dictionaries containing work history data.

    Returns:
        A JSON string representing the work history data.
    """
    workhistory = []
    count_jobs = None

    # Extract the work history data from the records
    for record in records:
        # Extract the job data from the record
        if not count_jobs:
            count_jobs = parse_php_serialized(record.get('meta_value'))
        title_value = (next
                       ((r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_title'), ""))
        company_value = (next
                         ((r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_company'), ""))
        experience_value = (next
                            ((r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_description'), ""))
        start_date_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_start_date'), "")
        end_date_value = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_end_date'), "")
        is_present = next(
            (r['meta_value'] for r in records if r['meta_key'] == 'jobsearch_field_experience_date_prsnt'), "")

        # Parse the title, company, experience
        titles = parse_php_serialized(title_value)
        companies = parse_php_serialized(company_value)
        experiences = parse_php_serialized(experience_value)
        start_dates = parse_php_serialized(
            start_date_value) or parse_php_serialized(start_date_value)
        end_dates = parse_php_serialized(
            end_date_value) or parse_php_serialized(end_date_value)

    # Process each education record
    for i in range(len(count_jobs)):
        title = titles[i]
        company = companies[i]
        experience = experiences[i]
        start_date = clean_date(start_dates[i])
        end_date = clean_date(end_dates[i])

        # Combine and format dates if both start and end dates are available
        if start_date and end_date:
            year = f"{start_date} - {end_date}"
        elif start_date and (is_present[i] or is_present[i] == 'on'):
            year = f"{start_date} - Present"
        else:
            year = start_date or end_date or ""

        # Remove HTML tags, special characters and formatting
        description = clean_description(experience)

        # Create the work history dictionary
        workhistory_data = {
            "title": title,
            "company": company,
            # "location": location,
            "duration": year,
            "description": description,
        }

        # Add the education data to the list
        workhistory.append(workhistory_data)

    # Directly return the list of parsed education records
    return workhistory if workhistory else None


def get_candidate_data(candidate_id):
    """
    Fetch candidate data from the MySQL database.
    Args:
        candidate_id (int): The ID of the candidate.
    Returns:
        dict: A dictionary containing the candidate's data.
    """
    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Get database connection details
    user = config['DATABASE']['USER']
    password = config['DATABASE']['PASSWORD']
    host = config['DATABASE']['HOST']
    database = config['DATABASE']['DATABASE']

    # Initialize an empty dictionary to store key-value pairs
    user_data = {}
    education_records = []
    workhistory_records = []

    try:
        # Establish a connection with mysql.connector.connect(user=user, password=password, host=host, database=database) as cnx:
        with mysql.connector.connect(user=user, password=password, host=host, database=database) as cnx:
            print("Connected successfully!")

            # Create a cursor with cnx.cursor(dictionary=True) as cursor:
            with cnx.cursor(dictionary=True) as cursor:
                # Execute a SELECT query with parameterized input
                query = "SELECT post_id, meta_key, meta_value FROM `itll_postmeta` WHERE post_id = %s"
                cursor.execute(query, (candidate_id,))

                # Fetch results and process the records
                for row in cursor.fetchall():
                    key = row["meta_key"]
                    value = row["meta_value"]
                    if not value:
                        continue

                    if key == "member_display_name":
                        user_data["name"] = value
                    elif key == "email" or key == "user_email_field":
                        user_data["email"] = value
                    elif key == "user_phone" or key == "jobsearch_field_user_phone":
                        user_data["phone"] = value
                    elif key == "jobsearch_cand_skills":
                        skills = parse_php_serialized(value)
                        user_data["skills"] = skills
                    elif key.startswith("jobsearch_field_edu"):
                        education_records.append(row)
                    elif key.startswith("jobsearch_field_exp"):
                        workhistory_records.append(row)

                # Check if all mandatory fields are present
                if "name" not in user_data or "email" not in user_data or "phone" not in user_data:
                    return {"error": "Candidate is missing one or more mandatory fields (name, email, phone)"}

                # Add parsed education data to user_data
                if education_records:
                    user_data["education"] = parse_education_records(
                        education_records)

                # Add parsed work history data to user_data
                if workhistory_records:
                    user_data["experience"] = parse_workhistory_records(
                        workhistory_records)

    # except mysql.connector.Error as err:
    #     print(f"Error: {err}")
    #     return {"error": f"Database connection error: {err}"}
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        # Raise an exception to propagate the error
        raise Exception(f"Database connection error: {err}")

    # Create a JSON string from the user data
    json_data = json.dumps(user_data, indent=4)
    return json_data
