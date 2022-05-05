import requests
import datetime
import time
import threading

# made by guoguoly
# 按需使用，请勿滥用

id = '' #一卡通号
pwd = ''#统一身份认证密码
class_flag = 1 #0是单人研讨间，1多人，2多人大间
tmp_day = '' #需要预约的日期，格式20211224，默认明天，

invideID = ['213161111','213171111'] #填受邀人一卡通号 按照预约研讨间大小添加人数

time_list = [['0800','0900'],['1320','1440'],] #注意是两个中括号 里面那个中括号表示需要预约的时间段 [['第一个开始时间','第一个结束时间'],['第二个开始时间','第二个结束时间']]
#时间范围   前两个数字表示小时，后两个表示分钟，间隔超过4小时需要手动拆分，预约时间大于等于1小时
#可以添加多个

gap_times = 1 #每轮搜索的间隔时间 （一轮指获取一次所有信息表，并依次尝试可能的预约选择后，多线程模式下会等本轮所有请求反馈结束后再开启下一轮）

threading_mode = 0
#多线程，输出显示可能会覆盖，看不到所有的信息，已是否预约到为准   0则单线程预约
#多线程下，比较可能不同时间预约的研讨间是不同的，需要确保几个时间段所预约的研讨间相同，则使用单线程预约，
#单人研讨间建议使用单线程，因为反馈请求的时间似乎挺快，单线程下预约反馈速度足够快了，而多人研讨间反馈请求的时间不知道为什么总会慢一些，卡住后续时间预约，所以建议使用多线程。

# countdown_mode = 0 #倒计时模式，卡零点自动预约后天的研讨间  未完成
# 2022-5-5懒得加了 就酱吧  
# 后来想起来好像应该需要加一个预约特定研讨间的功能（白名单or黑名单），应该加个判断就行了，但我懒得整了233333，
# 想加的在getinfo函数内，flag那对devName变量加个判断就行


mb_list = ''


def init(tmp_day,class_flag):
    # 一些数据的初始化
    today = datetime.datetime.today()
    # if countdown_mode:
    #     day = (today+datetime.timedelta(days=2)).strftime("%Y%m%d")
    if not tmp_day:
        day = (today+datetime.timedelta(days=1)).strftime("%Y%m%d")
    else:
        day = tmp_day
    if class_flag==1:
        min_user = 2
        max_user = 6
    elif class_flag==2:
        min_user = 4
        max_user = 10
    else:
        min_user = ''
        max_user = ''
    class1 = ['100417753','108009514','108305607']
    class_f = class1[class_flag]
    url1 = f"http://10.9.4.215/ClientWeb/pro/ajax/device.aspx?classkind=1&display=cld&md=d&class_id={class_f}&cld_name=default&date={day}&act=get_rsv_sta&"
    return url1,class_f,day,min_user,max_user


def getsession(id,pwd):
    # IC系统登录
    header = {
    'Accept':'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Connection':'keep-alive',
    'Content-Length':'33',
    'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
    'Host':'10.9.4.215',
    'Origin':'http://10.9.4.215',
    'Referer':'http://10.9.4.215/ClientWeb/xcus/ic2/Default.aspx',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
    'X-Requested-With':'XMLHttpRequest',
    }
    login_url = "http://10.9.4.215/ClientWeb/pro/ajax/login.aspx"
    session = requests.session()
    Data = {
        'id': id,
        'pwd': pwd,
        'act': 'login'
    }
    r2 = session.post(login_url,headers=header,data=Data).text
    if '"msg":"ok"' in r2:
        print("登录成功")
    else:
        print("登录可能遇到错误")
    return session

def searchId(session,id,invideID):
    # 一卡通号转化为invideID 并化为请求需要的格式
    a = '$'+session.get(f'http://10.9.4.215/ClientWeb/pro/ajax/data/searchAccount.aspx?type=&ReservaApply=ReservaApply&term={id}').json()[0]['id']+','
    for i in invideID:
        a += (session.get(f'http://10.9.4.215/ClientWeb/pro/ajax/data/searchAccount.aspx?type=&ReservaApply=ReservaApply&term={i}').json()[0]['id'])+','
    return a[:-1]

def getinfo(url1,time_list):
    global thread_list
    for i in requests.get(url1).json()['data']:# 研讨间
        devName,devID,labId,kindId = i['devName'],i['devId'],i['labId'],i['kindId']
        # print(devName,devID,labId,kindId)
        for time1 in time_list: #每一个期望时间
            flag = 1
            for ii in i['ts']: #当前研讨间已有的预约
                start1 = int(ii['start'][-5:-3]+ii['start'][-2:])
                end1 = int(ii['end'][-5:-3]+ii['end'][-2:])
                # 判断当前研讨间时间是否可以预约
                if ((start1-int(time1[0]))*(end1-int(time1[0]))>=0) and ((start1-int(time1[1]))*(end1-int(time1[1]))>=0) and (not start1==int(time1[0])) and (not end1==int(time1[1])):
                    continue
                else:
                    flag = 0
                    break
            if flag:
                print(f'开始预约{devName},时间{time1}')
                if threading_mode:
                    t = threading.Thread(target=yuyue, args=(session,devID,labId,kindId,time1,mb_list,devName))
                    thread_list.append(t)
                    t.start()
                else:
                    r2 = yuyue(session,devID,labId,kindId,time1,mb_list,devName)
                    print(r2)
                    

def yuyue(session,dev_id,lab_id,kind_id,time1,mb_list,devName):
    global time_list
    start1 = datetime.datetime.strptime(day, "%Y%m%d").strftime("%Y-%m-%d")+' '+time1[0][:2]+':'+time1[0][2:]
    end1 = datetime.datetime.strptime(day, "%Y%m%d").strftime("%Y-%m-%d")+' '+time1[1][:2]+':'+time1[1][2:]
    set_url = "http://10.9.4.215/ClientWeb/pro/ajax/reserve.aspx?"
    Data2 = {
        'dev_id':dev_id,
        'lab_id':lab_id,
        'kind_id':kind_id,
        'type':'dev',
        'start':start1,
        'end':end1,
        'start_time':time1[0],
        'end_time':time1[1],
        'act':'set_resv',
        'mb_list': mb_list,
        'min_user': min_user,
        'max_user': max_user
    }
    r2 = session.get(set_url,data=Data2).text
    # print(r2)
    
    if "操作成功" in r2:
        print(f"{devName}{start1}到{end1}预约成功")
        try:
            time_list.remove(time1)
        except:
            pass
        finally:
            pass
    if "已有预约" in r2:
        print("同时段已有预约")
        try:
            time_list.remove(time1)
        except:
            pass
        finally:
            pass
    return r2

if __name__=="__main__":
    session = getsession(id,pwd)
    if class_flag:
        mb_list = searchId(session,id,invideID)
        print(mb_list)
    url1,class_f,day,min_user,max_user = init(tmp_day,class_flag)
    while time_list:
        thread_list = []
        getinfo(url1,time_list)
        print(time_list)
        for t in thread_list:
            t.join()
        time.sleep(gap_times)
    print("预设时间列表已经预约完成")
