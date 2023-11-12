from flask import Flask, request, jsonify, Response
from datetime import datetime
from main import db

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

