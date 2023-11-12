# project: p4
# submitter: hliu656
# partner: none
# hours: 6.5

import pandas as pd
from flask import Flask, request, jsonify, Response
import flask
import re 
from io import BytesIO
import time
import matplotlib.pyplot as plt 
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

app = Flask(__name__)
mongo_url = "mongodb+srv://mingruzhu01:GBfvriyxKr2XKT8e@cluster0.jqldqw3.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_url)
db = client["madHack"]
#db = client["madHack"]

ABcount = 0
Avisit = 0
Bvisit = 0
last_request_time = dict()
visitor_ips = []
num_subscribed = 0


df = pd.read_csv("main.csv")


def scatter_plot(x, xlabel, y, ylabel, title):
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    img_bytes = BytesIO()
    ax.get_figure().savefig(img_bytes, format='svg')
    plt.close()
    return img_bytes.getvalue()

# Function to create histogram plot
def histogram_plot(x, xlabel, title):
    fig, ax = plt.subplots()
    ax.hist(x)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    img_bytes = BytesIO()
    ax.get_figure().savefig(img_bytes, format='svg')
    plt.close()
    return img_bytes.getvalue()

# Function to create box plot
# def box_plot(x, title):
#     fig, ax = plt.subplots()
#     ax.boxplot(x)
#     ax.set_xlabel("X")
#     ax.set_ylabel("Y")
#     ax.set_title(title)
#     img_bytes = BytesIO()
#     ax.get_figure().savefig(img_bytes, format='svg', bbox_inches="tight")
#     plt.close()
#     return img_bytes.getvalue()

@app.route('/login.html')
def login_handler():
    global a
    with open("login.html") as f:
        html = f.read()
    return html


@app.route("/temperature.svg")
def temperature():
    type = request.args["type"]
    if type == "scatter":
        plot = scatter_plot(df["date_day"], "date_day", df["tavg"], "tavg", "Scatter Plot of average temperature by day")
    elif type == "histogram":
        plot = histogram_plot(df["tavg"], "tavg", "histogram_plot of average temperature by frequences")
    return Response(plot,
                    headers={"Content-Type": "image/svg+xml"})

@app.route("/snow.svg")
def snow():
    plot = scatter_plot(df["date_day"], "date_day", df["snow_depth"], "snow_depth", "Scatter Plot of snowy depth by day")
    return Response(plot,
                    headers={"Content-Type": "image/svg+xml"})
    
    
user_data = {
    "user1": "password1",
    "user2": "password2"
}

@app.route('/create_account', methods=['POST'])
def create_acount():
    # 创建一个新用户
    users_collection = db['User']
    username = request.form.get('username')
    if not username:
        print("no username")
    email = request.form.get('email')
    password = request.form.get('password')
    print("here2")
    user = users_collection.find_one({"username": username})
    print("here3")
    if user:
        print("找到用户：", user)
        return jsonify(success=False)
    else:
        new_user = {
            "username": username,
            "email": email,
            "password": password,  # 注意：实际应用中应使用哈希密码
            "register_date": datetime.utcnow(),
            "last_login_time": datetime.utcnow(),
            "status": "active"
        }
    # 将新用户插入到 MongoDB 集合
        users_collection.insert_one(new_user)
        return jsonify(success=True)

@app.route('/create_account.html')
def create_account_page():
    with open("create_account.html") as f:
        html = f.read()
    return html

@app.route('/submit', methods=['POST'])
def login():
    users_collection = db['User']
    username = request.form.get('username')
    password = request.form.get('password')
    user = users_collection.find_one({"username": username})
    if user and user['password'] == password:
        print("yeah")
        return jsonify(success=True)
    else:
        return jsonify(success=False)


@app.route('/')
def home():
    with open("index.html") as f:
        html = f.read()
        
    global ABcount
    version_A = "<p><a href=\"donate.html?from=A\">Donation</a></p>"
    version_B = "<p><a href=\"donate.html?from=B\">Please donate us!</a></p>"
    default = "<p><a href=\"donate.html\">donate here</a></p>"
    search_str = "</body>"
    image = """
    <img src="temperature.svg?type=histogram"><br><br>
    <img src="temperature.svg?type=scatter"><br><br>
    <img src="snow.svg"><br><br>
    <p><a href="browse.html">browse</a></p>
    """
    pos = html.find(search_str)
    if ABcount < 10:
        if ABcount%2 == 0:
            ABcount += 1
            return html[:pos] + version_A + image + html[pos:]
        else: 
            ABcount += 1
            return html[:pos] + version_B + image + html[pos:]
    else:
        if Avisit >= Bvisit:
            return html[:pos] + version_A + image + html[pos:]
        if Avisit < Bvisit:
            return html[:pos] + version_B + image + html[pos:]
    
    return html[:pos] + default + image + html[pos:]

@app.route('/browse.html')
def browse_handler():
    global a
    html = """
    <html>
      <body>
            <h1>madison weather official 2020</h1>
            <p>Enjoy the data!</p>
                {}
      </body>
    </html>
    """
    return html.format(df.to_html())

@app.route('/browse.json')
def browse_json_handler():
    global df, last_request_time
    ip = request.remote_addr
    if ip in last_request_time and time.time() - last_request_time[ip] < 60:
        time_del = time.time() - last_request_time[ip]
        return flask.Response("<b>go away</b>",
                          status=429,
                          headers={"Retry-After": time_del})

    last_request_time[ip] = time.time()
    visitor_ips.append(ip)
    data = df.to_dict('records')
    return jsonify(data)

@app.route('/visitors.json')
def visitors_handler():
    global visitor_ips
    return jsonify(visitor_ips)


@app.route('/email', methods=["POST"])
def email():
    global num_subscribed
    email = str(request.data, "utf-8")
    if len(re.findall(r"\b^[^@]{1,}@[^@]{1,}\..{1,3}\b", email)) > 0: # 1
        with open("emails.txt", "a") as f: # open file in append mode
            f.write(email + "\n") # 2
            num_subscribed += 1
        return jsonify(f"thanks, your subscriber number is {num_subscribed}!")
    return jsonify(f"Illegal email address\nplease check your email address") # 3
                    

@app.route("/donate.html")
def handler2():
    global Avisit, Bvisit
    try:
        version = request.args["from"]
        if version == "A":
            Avisit += 1
        if version == "B":
            Bvisit += 1
    except:
        pass
    with open("donate.html") as f:
        html = f.read()
    return html


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.