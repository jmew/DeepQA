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
        print(df_req)
        sentence = df_req['queryText']
        output = felix.predict(sentance)
        return jsonify(
            fulfillmentText=output,
        )


if __name__ == '__main__':
    felix = chatbot_api.Chatbot()
    felix.run()
    app.run(host='0.0.0.0', port='5002')
