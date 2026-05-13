from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json
import os

# Flask app
app = Flask(__name__)

# Enable CORS
CORS(app)

# Configure Groq API (using OpenAI client)
client = openai.OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://api.groq.com/openai/v1"
)

# Recipe API Route
@app.route("/recipe", methods=["POST"])
def recipe():
    try:
        # Get frontend data
        data = request.get_json()
        recipe_name = data.get("recipe", "Something tasty")

        # AI prompt
        prompt = f"""
        Generate a detailed recipe for {recipe_name}.

        Return ONLY valid JSON. Do not include markdown code blocks.

        Example format:

        {{
            "name": "Pizza",
            "description": "Cheesy homemade pizza",
            "prep": "15 mins",
            "cook": "20 mins",
            "ingredients": [
                "Flour",
                "Cheese",
                "Tomato Sauce"
            ],
            "steps": [
                "Prepare dough",
                "Add toppings",
                "Bake pizza"
            ]
        }}
        """

        # Generate AI response using Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Groq model
            messages=[
                {"role": "system", "content": "You are a professional chef. You only output valid JSON recipes."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" } # Forces valid JSON
        )

        ai_response = response.choices[0].message.content

        # Clean markdown formatting just in case
        ai_response = ai_response.replace("```json", "")
        ai_response = ai_response.replace("```", "")
        ai_response = ai_response.strip()

        # Convert AI text → JSON
        recipe_json = json.loads(ai_response)

        # Normalize ingredients: convert any objects to strings
        if "ingredients" in recipe_json:
            clean_ingredients = []
            for item in recipe_json["ingredients"]:
                if isinstance(item, dict):
                    clean_ingredients.append(" ".join(str(v) for v in item.values()))
                else:
                    clean_ingredients.append(str(item))
            recipe_json["ingredients"] = clean_ingredients

        # Normalize steps: convert any objects to strings
        if "steps" in recipe_json:
            clean_steps = []
            for item in recipe_json["steps"]:
                if isinstance(item, dict):
                    clean_steps.append(" ".join(str(v) for v in item.values()))
                else:
                    clean_steps.append(str(item))
            recipe_json["steps"] = clean_steps

        # Send response to frontend
        return jsonify(recipe_json)

    except Exception as e:
        print("ERROR:", e)
        
        # Fallback error response
        return jsonify({
            "name": recipe_name.title() if 'recipe_name' in locals() else "Mock Recipe",
            "description": f"OpenAI API Error: {str(e)}",
            "prep": "0 mins",
            "cook": "0 mins",
            "ingredients": [
                "Error Occurred"
            ],
            "steps": [
                "Please check your OpenAI API key and billing."
            ]
        })

# Run Flask server
if __name__ == "__main__":
    app.run(debug=True, port=5001)