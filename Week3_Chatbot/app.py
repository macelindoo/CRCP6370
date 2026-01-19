#Import Necessary Libraries
from flask import Flask, render_template, request

# Creating Flask App
app = Flask(__name__)

# Simple Bot Logic Function (def): take user input and return a response
def get_bot_response(user_input):
    # Simple logic for testing purposes. Look for hello or joke in user input.
    if "hello" in user_input.lower():
        return "Hello! How can I help you today?"
    elif "joke" in user_input.lower():
        return "Why did the computer show up at work late? It had a hard drive!"
    else:
        return f"You said: {user_input}"

# Route for Chat Interface
# 1. When someone visits the root URL ("/"), show them the chat interface.
# 2. If they submit a message (POST request), get the bot response and display it.
@app.route("/", methods=["GET", "POST"])
# 3. Create chat function to handle requests and responses using the chat.html template.
def chat():
    bot_response = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        bot_response = get_bot_response(user_input)
    return render_template("chat.html", bot_response=bot_response)

# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)