from flask import Flask, request, jsonify
from flask_restful import Api
from chatbot import chatbot_api


app = Flask(__name__)
api = Api(app)
felix = None

@app.route('/', methods=['POST']) #allow both GET and POST requests
def form_example():
    if request.method == 'POST':  #this block is only entered when the form is submitted
        req_data = request.get_json()
        df_req = req_data['queryResult']
        sentence = df_req['queryText']
        output = felix.predict(sentence)
        print(output)
        return jsonify(fulfillmentText=output)

questions = ["will", "would", "could", "can", "is", "are", "am"];

def add_missing_punc(s):
    # TODO
    mod_s = s
    if len(s) == 0:
        return mod_s

    words = s.lower().split()
    if words[0] in questions:
        if s[-1] != "?":
            mod_s += "?"
    else if s[-1] != "!" and s[-1] != ".":
        mod_s += "."

    return mod_s

if __name__ == '__main__':
    felix = chatbot_api.Chatbot()
    felix.run()
    app.run(host='0.0.0.0', port='5002')
