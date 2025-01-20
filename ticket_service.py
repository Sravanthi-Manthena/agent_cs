import os
import re
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import datetime
import random
import string

# Load environment variables
load_dotenv()

# Initialize the LLM using the Groq API
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("Groq API key not found. Please set the environment variable.")

llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",  # You can change the model here if needed
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=groq_api_key
)

# Simulated responses for LLM functionality
def get_answer_from_query(query, selected_module):
    prompt = f"The user is facing an issue in the SAP {selected_module} module. The issue is as follows: {query}. Please provide a solution for this problem."
    messages = [{"role": "user", "content": prompt}]
    response = llm.invoke(messages)
    return response.content

def generate_ticket_id():
    # Generate a random ticket ID (You can adjust the length as per your need)
    ticket_id = ''.join(random.choices(string.digits, k=8))  # 8-digit ticket ID
    return ticket_id

def generate_user_id():
    # Generate a random uppercase letter
    letter = random.choice(string.ascii_uppercase)
    # Generate 5 random digits
    digits = ''.join(random.choices(string.digits, k=5))
    # Combine the letter and digits
    user_id = f"{letter}{digits}"
    return user_id
 

def extract_details_from_input(user_input):
    prompt = f"""
    The user has provided the following request:
    '{user_input}'
    Please extract the following information:
    1. ticket_name
    2. ticket_description
    3. ticket_type
    4. module
    5. priority
    6. category
    """

    messages = [{"role": "user", "content": prompt}]
    
    # Assuming llm.invoke is calling a language model API, the response needs to be handled properly
    response = llm.invoke(messages)

    # Assuming response.content is the string or JSON response returned by the model
    extracted_info = {}

    # Here, assuming the response is text-based and we need to parse it
    if response and response.content:
        content = response.content.strip()

        # Example approach to parsing (you may want to adjust this based on how the response is structured)
        try:
            # Attempting to parse the returned content
            # Example: Expecting something like "ticket_name: 'Issue'; ticket_description: '...' etc."
            for line in content.split("\n"):
                if 'ticket_name' in line:
                    extracted_info['ticket_name'] = line.split(":", 1)[1].strip().strip("'")
                elif 'ticket_description' in line:
                    extracted_info['ticket_description'] = line.split(":", 1)[1].strip().strip("'")
                elif 'ticket_type' in line:
                    extracted_info['ticket_type'] = line.split(":", 1)[1].strip().strip("'")
                elif 'module' in line:
                    extracted_info['module'] = line.split(":", 1)[1].strip().strip("'")
                elif 'priority' in line:
                    extracted_info['priority'] = line.split(":", 1)[1].strip().strip("'")
                elif 'category' in line:
                    extracted_info['category'] = line.split(":", 1)[1].strip().strip("'")

        except Exception as e:
            # Log the exception or handle it as needed
            print(f"Error parsing the response: {e}")
    
    return extracted_info


def predict_and_parse_sap_error_details(error_message):
    """
    Predicts the SAP module, category, ticket type, error description, error code, and priority based on the user-provided error message.
    LLM is called to predict these details, and the response is parsed into separate values.
    """
    prompt = f"""
    Based on the following SAP error message: "{error_message}",
    please predict the following details in a structured format:
    
    - SAP Module (e.g., Financial Accounting, SAP FICO)
    - Category (e.g., Configuration, Master Data, Security, Basis, Technical)
    - Ticket Type (e.g., Service, Incident)
    - Error Description (brief description of the error)
    - Error Code (if available, provide an error code)
    - Priority (e.g., Critical, High, Medium, Low)
    
    Do not provide any additional information or context. Just return the values for the fields listed above.
    """

    # LLM invocation with the above structured prompt
    messages = [{"role": "user", "content": prompt}]
    response = llm.invoke(messages)

    # Parse the LLM response using regular expressions
    response_str = response.content
    details = {}

    try:
        # Using regular expressions to extract details from the LLM response
        module_match = re.search(r"SAP Module\s*[:\-]?\s*([A-Za-z\s\(\)]+)", response_str)
        category_match = re.search(r"Category\s*[:\-]?\s*([A-Za-z\s,/\(\)]+)", response_str)
        ticket_type_match = re.search(r"Ticket Type\s*[:\-]?\s*([A-Za-z\s,/\(\)]+)", response_str)
        error_description_match = re.search(r"Error Description\s*[:\-]?\s*([A-Za-z0-9\s,\.]+)", response_str)
        error_code_match = re.search(r"Error Code\s*[:\-]?\s*([A-Za-z0-9\s'\/]+)", response_str)
        priority_match = re.search(r"Priority\s*[:\-]?\s*([A-Za-z\s]+)", response_str)

        # Assigning matched values to the dictionary, or 'Unknown' if not found
        details['module'] = module_match.group(1).strip() if module_match else 'Unknown Module'
        details['category'] = category_match.group(1).strip() if category_match else 'Unknown Category'
        details['ticket_type'] = ticket_type_match.group(1).strip() if ticket_type_match else 'Unknown Type'
        details['error_description'] = error_description_match.group(1).strip() if error_description_match else 'Unknown Description'
        details['error_code'] = error_code_match.group(1).strip() if error_code_match else 'Unknown Code'
        details['priority'] = priority_match.group(1).strip() if priority_match else 'Medium'  # Default priority to Medium if not found

        # Return the fields separately
        return details['module'], details['ticket_type'], details['error_description'], details['category'], details['priority'], details['error_code']
    
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        # Return 'Unknown' values in case of an error
        return 'Unknown Module', 'Unknown Type', 'Unknown Description', 'Unknown Category', 'Medium', 'Unknown Code'


# Ticket creation function
def ticket_info(user_id, query):
    # Extract details from the SAP error message using the prediction function
    module, ticket_type, error_description, category, priority, error_code = predict_and_parse_sap_error_details(query)

    # Generate a ticket name (you can customize this as needed)
    ticket_name = f"Ticket for {module} - {error_code if error_code != 'Unknown Code' else 'General Issue'}"

    # Get current time and format it as YYYY-MM-DD HH:MM:SS
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    

    # Create the ticket details as a dictionary
    ticket_details = {
        "user_id": user_id,
        "ticket_name": ticket_name,
        "ticket_description": error_description,
        "ticket_type": ticket_type,
        "module": module,
        "priority": priority,
        "category": category,
        "status": "Open",  # Initial status as Open
        "ticket_id": None,  # Placeholder for ticket ID (if database is available later)
        "timestamp": timestamp  # Formatted timestamp
    }

    # You can return this dictionary to simulate ticket creation
    return ticket_details



# Internal function to create a ticket
def create_ticket(details):
    # Print a message indicating the ticket has been created, along with the ticket details
    print(f"Ticket has been created with these details: {details}")
    return {"status": "success", "ticket_details": details}