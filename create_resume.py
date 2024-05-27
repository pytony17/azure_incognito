"""
This program takes the json resume info from incognito.careers and creates an AI-enhanced resume
using elaborate prompt. The resume is then saved in Word doc format.

Instead of gpt-3.5-turbo or gpt-4, this version of create_resume uses Anthropic's Claud model.

"""
# Standard library imports
import configparser
import json
import os

# Related third party imports
from anthropic import Anthropic  # Import Anthropic library


def fix_resume_bullets(resume_text):
    """Replaces "-" at the beginning of a line with a bullet point symbol.

    Args:
        resume_text: The text of the resume.

    Returns:
        The text of the resume with fixed bullet points.
    """
    lines = resume_text.splitlines()
    fixed_lines = []
    for line in lines:
        if line.startswith("-"):
            fixed_lines.append("• " + line[1:])
        else:
            fixed_lines.append(line)
    return "\n".join(fixed_lines)


def generate_resume(candidate_info):
    """
    Generates a resume using Anthropic's Claude LLM.

    Args:
        candidate_info: A dictionary containing the applicant's information.

    Returns:
        The generated resume as a string.
    """

    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Get Anthropic api key
    api_key = config['LLM']['ANTHROPIC_KEY']

    client = Anthropic(
        api_key=api_key,
    )

    # Convert candidate info to JSON string
    candidate_info_json = json.dumps(candidate_info)

    # Define the prompt message
    prompt = f"""Considering the following applicant information provided in JSON format:
    {candidate_info_json} 
    Craft a compelling, one-page resume that showcases their diverse skills and accomplishments. Utilize a professional template and highlight transferable skills throughout the resume, demonstrating their value across various industries and positions.

    Here's what you should leverage from the JSON data:

    Personal Information: Name, contact details (phone, email, optional: LinkedIn profile URL)
    Skills: List of hard skills (software proficiency, technical skills) and soft skills (communication, leadership)
    Work History:
    Company Name, Start & End Dates, Job Title
    Key Achievements (quantify results whenever possible using numbers, percentages, etc.)
    Education Background: University Name, Degree Obtained, Relevant Coursework or Projects (optional)
    Incorporating Transferable Skills:

    Analyze the applicant's work history and education to identify transferable skills that are valuable across different fields.
    Instead of a separate section, seamlessly integrate these transferable skills into the descriptions of each job experience. Highlight how these skills were utilized to achieve accomplishments.
    Polishing the Resume:

    Maintain a clear and concise format with easy-to-read fonts and headings and bullet point lists.
    Employ strong action verbs to describe accomplishments.
    Remove the "Transferable Skills and Suggestions" and "Additional Information" sections. Their content should be incorporated into the existing sections.
    Proofread meticulously for any grammatical errors or typos.
    By following these guidelines and leveraging the applicant's JSON data, generate a comprehensive and finished professional resume that positions them as a strong candidate for various opportunities.
    Return the resume in text format.
    """

    prompt_message = {"role": "user", "content": prompt}

    # Availalble Claude 3 models
    # Claude 3 Opus	    claude-3-opus-20240229
    #                   Most powerful model, delivering state-of-the-art performance on highly complex tasks and demonstrating fluency and human-like understanding
    # Claude 3 Sonnet	claude-3-sonnet-20240229
    #                   Most balanced model between intelligence and speed, a great choice for enterprise workloads and scaled AI deployments
    # Claude 3 Haiku	claude-3-haiku-20240307
    #                   Fastest and most compact model, designed for near-instant responsiveness and seamless AI experiences that mimic human interactions

    # Send the prompt to Claude and get the response
    response = client.messages.create(
        messages=[prompt_message],
        max_tokens=4096,
        model="claude-3-haiku-20240307",
        temperature=1.0,
    )

    resume = fix_resume_bullets(response.content[0].text)

    return resume
