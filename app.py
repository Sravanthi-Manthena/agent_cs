from flask import Flask, request, jsonify, session, render_template
from ticket_service import get_answer_from_query,generate_user_id, generate_ticket_id, predict_and_parse_sap_error_details, ticket_info, extract_details_from_input

from datetime import datetime
 
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

 
@app.route('/')
def home():
    return render_template('index1.html')
 
@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    data = request.get_json()
    user_input = data.get('user_input', '').strip().lower()
    conversation_started = data.get('conversation_started', False)
 
    user_id = generate_user_id()
 
    if not conversation_started:
        initial_greeting = "Hi, I am Amelia, the customer service agent. I will help you in resolving errors. How can I help you?"
        return jsonify({"greeting_message": initial_greeting, "solution": ""})
 
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'howdy', 'greetings']
   
    if any(greeting in user_input for greeting in greetings):
        greeting_response = "Hello! How can I assist you today? Please provide the error or issue you need help with."
        return jsonify({"greeting_message": greeting_response, "solution": ""})
 
    module, ticket_type, error_description, category, priority, error_code = predict_and_parse_sap_error_details(user_input)
 
    session['last_query'] = user_input
 
    if "Unknown" not in [module, ticket_type, error_description, category, priority, error_code]:
        solution = get_answer_from_query(user_input, module)
        return jsonify({
            "greeting_message": "",
            "module": module,
            "ticket_type": ticket_type,
            "error_description": error_description,
            "category": category,
            "priority": priority,
            "error_code": error_code,
            "solution": solution,
            "resolved_question": "Is the issue resolved? (yes/no)"
        })
 
    solution = get_answer_from_query(user_input, "General")
    return jsonify({
        "greeting_message": "",
        "solution": solution,
        "resolved_question": "Is the issue resolved? (yes/no)"
    })
 
@app.route('/resolve_issue', methods=['POST'])
def resolve_issue():
    data = request.get_json()
    user_input = data.get('user_input', '').strip().lower()
    user_id = data.get('user_id', generate_user_id())
 
    positive_responses = ['yes', 'yeah', 'yep', 'sure', 'of course', 'correct', 'absolutely']
 
    if any(response in user_input for response in positive_responses):
        session['resolved'] = 'yes'
        return jsonify({
            "greeting_message": "",
            "solution": "Great, thank you! Have a great day! Is there anything else I can assist you with?"
        })
 
    elif user_input == "no":
        return jsonify({
            "greeting_message": "",
            "solution": "Sorry for the inconvenience. Would you like me to raise a ticket for you?"
        })
 
    last_query = session.get('last_query', '')
    ticket_details = ticket_info(user_id, last_query)
   
    formatted_ticket_details = f"""Here are your ticket details:
 
Ticket Name: {ticket_details['ticket_name']}
Description: {ticket_details['ticket_description']}
Priority: {ticket_details['priority']}
Category: {ticket_details['category']}
Module: {ticket_details['module']}
 
Do you confirm this ticket creation? (yes/no)"""
 
    return jsonify({
        "greeting_message": "",
        "solution": formatted_ticket_details
    })
 
@app.route('/confirm_ticket', methods=['POST'])
def confirm_ticket():
    data = request.get_json()
    user_input = data.get('user_input', '').strip().lower()
    user_id = data.get('user_id', generate_user_id())
   
    if session.get('ticket_created'):
        return jsonify({
            "solution": "A ticket has already been created for this issue.",
            "ticket_details": session.get('ticket_details')
        })
 
    if "yes" in user_input:
        last_query = session.get('last_query', '')
        ticket_details = ticket_info(user_id, last_query)
        try:
            # Generate a random ticket_id
            ticket_id = generate_ticket_id()
            ticket_details['ticket_id'] = ticket_id
           
            session['ticket_created'] = True
            session['ticket_details'] = ticket_details
           
            return jsonify({
                "solution": "Great, ticket has been created successfully!",
                "ticket_details": ticket_details
            })
        except Exception as e:
            return jsonify({
                "error": f"Failed to create ticket: {str(e)}",
                "solution": "There was an error creating your ticket. Please try again."
            })
 
    elif "no" in user_input:
        return jsonify({
            "solution": "Please provide the details for updation."
        })
 
    return jsonify({
        "solution": "I didn't quite understand that. Please answer with 'yes' or 'no'."
    })
 
@app.route('/change-the-information', methods=['POST'])
def change_information():
    try:
        data = request.get_json()
       
        if not data:
            return jsonify({
                "success": False,
                "message": "No update information provided"
            }), 400
 
        updates = data.get('updates', {})
        ticket_id = data.get('ticket_id')
       
        current_ticket = session.get('ticket_details', {
            'user_id': 12345,
            'ticket_name': 'Default Ticket',
            'ticket_description': 'Default Description',
            'ticket_type': 'Incident',
            'module': 'General',
            'priority': 'Medium',
            'category': 'General',
            'status': 'Open',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
 
        for field, value in updates.items():
            if field in current_ticket:
                current_ticket[field] = value
 
        session['ticket_details'] = current_ticket
 
        if ticket_id and db_service:
            try:
                db_service.update_ticket(ticket_id, current_ticket)
            except Exception as e:
                print(f"Database update error: {str(e)}")
                return jsonify({
                    "success": False,
                    "message": f"Database error: {str(e)}"
                }), 500
 
        return jsonify({
            "success": True,
            "message": "Ticket information updated successfully",
            "ticket_details": current_ticket
        }), 200
 
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating ticket: {str(e)}"
        }), 500
 
if __name__ == '__main__':
    app.run(debug=True)