from bottle import Bottle, run, request, response
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker,declarative_base
from datetime import datetime,date,timedelta
import json
import threading
import time


# 设置数据库连接
with open("./src/password.txt","r") as file:
    password=file.readline()
    file.close

DATABASE_URL = 'mysql+pymysql://ledgerAndroid:{}@xxx.xxx.xxx.xxx/ledgerAndroid'.format(password)
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# 定义一个模型
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True)
    username = Column(String(16))
    password = Column(String(64))
    token = Column(String(64))

class Ledger(Base):
    __tablename__ = 'ledger'
    id = Column(Integer,primary_key=True)
    username = Column(String(16))
    type_ = Column(String(3))
    num = Column(Integer)
    time_ = Column(Date,default=datetime.now().date())

    
Base.metadata.create_all(engine)
# 创建一个会话
Session = sessionmaker(bind=engine)
session = Session()

def KeepAlive():
    while True:
        session.execute("SELECT 1")
        time.sleep(14400)

aliveThread=threading.Thread(target=KeepAlive)
aliveThread.setDaemon=True
aliveThread.start()

# 创建 Bottle 应用
ledgerAndroidAPI = Bottle()

#login
@ledgerAndroidAPI.route("/login",method="POST")
def login():
    try:
        response.content_type="application/json"
        data=request.json
        username=data["username"]
        password=data["password"]
        users=session.query(User)
        targetUser=users.filter(User.username==username,User.password==password).first()
        if targetUser:
            return json.dumps({"code":1,"token":targetUser.token})
        return json.dumps({"code":0,"token":"用户不存在或密码不正确"})
    except ValueError as e:
        return e
#upload
@ledgerAndroidAPI.route("/upload",method="POST")
def upload():
    try:
        response.content_type="application/json"
        data=request.json
        token=data["token"]
        num=data["num"]
        type_=data["type"]
        users=session.query(User)
        targetUser=users.filter(User.token==token).first()
        if targetUser:
            username=targetUser.username
            new_leger_item=Ledger(username=username,num=num,type_=type_)
            session.add(new_leger_item)
            session.commit()
            return json.dumps({"code":1,"msg":"添加成功"},ensure_ascii=False)
        session.commit()
        return json.dumps({"code":0,"msg":"添加失败"},ensure_ascii=False)
    except ValueError as e:
        return e
#get
@ledgerAndroidAPI.route("/getitems",method="GET")
def getItem():
    try:
        response.content_type="application/json"
        data=request.json
        token = data["token"]
        specific_date_list = data["specificDate"].split("-")
        year=int(specific_date_list[0])
        month=int(specific_date_list[1])
        day=int(specific_date_list[2])
        if not session.query(User).filter(User.token==token).first():
            return json.dumps({"code":0,"msg": "无法匹配用户|检查TOKEN"},ensure_ascii=False)
        method_= data["method"]
        if method_==0: #获取日数据
            specific_date = date(year,month,day)
            query = session.query(Ledger).filter(Ledger.time_==specific_date)
            results = query.all()
            if not results:
                return json.dumps({"code":0,"items":[],"total":""})
            results_items = [{"num":item.num,"type_":item.type_,"time_":item.time_.isoformat()} for item in results]
            total = sum([i["num"] for i in results_items])
            return json.dumps({"code":1,"items":results_items,"total":total},ensure_ascii=False)
        if method_==1: #获取近七天数据
            end_day=datetime.now().date()
            start_day=end_day-timedelta(days=6)
            query = session.query(Ledger).filter(Ledger.time_ >= start_day, Ledger.time_ <= end_day)
            results = query.all()
            if not results:
                return json.dumps({"code":0,"items":[],"total":""})
            results_items = [{"num":item.num,"type_":item.type_,"time_":item.time_.isoformat()} for item in results]
            total = sum([i["num"] for i in results_items])
            return json.dumps({"code":1,"items":results_items,"total":total},ensure_ascii=False)
        if method_==2: #获取月数据
            start_day=date(year,month,1)
            bigmonth=[1,3,5,7,8,10,12]
            if month in bigmonth:
                end_day=date(year,month,31)
            else:
                end_day=date(year,month,30)
            query = session.query(Ledger).filter(Ledger.time_ >= start_day, Ledger.time_ <= end_day)
            results = query.all()
            if not results:
                return json.dumps({"code":0,"items":[],"total":""})
            results_items = [{"num":item.num,"type_":item.type_,"time_":item.time_.isoformat()} for item in results]
            total = sum([i["num"] for i in results_items])
            return json.dumps({"code":1,"items":results_items,"total":total},ensure_ascii=False)
    except ValueError as e:
        return e

#test
@ledgerAndroidAPI.route("/test",method="GET")
def test():
    return "ok!"
