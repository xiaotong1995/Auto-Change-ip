import requests
import random
import time
import logging
ipflag=0
num=0
def getlogger():
    # 第一步，创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关
    # 第二步，创建一个handler，用于写入日志文件
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # 输出到console的log等级的开关
    # 第三步，定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    # 第四步，将logger添加到handler里面
    logger.addHandler(ch)
def get_ip_list(path):
    iplist=[]
    with open(path, "r") as f:
        for line in f.readlines():
            iplist.append(tuple(eval(line.strip())))
    logging.info("在文件：{}中共获取到{}个备用ip".format(path,str(len(iplist))))
    return iplist
def get_ip(iplist):
    global num
    if num>=len(iplist):
        num=0
    while True:
        ip = iplist[num][0]
        num=num+1
        if if_ip_qiang(ip):
            break
    return ip
def if_ip_qiang(ip):
    api = "http://{}/cdn-cgi/trace".format(ip)
    try:
        req = requests.get(api, timeout=3)
        if ip in req.text:
            logging.info("此ip：{}访问正常".format(ip))
        flag=True
    except:
        #重试一次
        try:
            logging.info("此ip：{}访问异常，重试一次".format(ip))
            req = requests.get(api, timeout=3)
            logging.info("此ip：{}访问正常".format(ip))
            flag = True
        except:
           logging.info("此ip：{}访问异常，请手动检查".format(ip))
           flag = False
    return flag
def if_ip_qiang2(ip):
    url="http://"+ip
    try:
        req = requests.get(url, timeout=5)
        logging.info("此ip：{}访问正常".format(ip))
        flag=True
    except:
        #重试一次
        try:
            logging.info("此ip：{}访问异常，重试一次".format(ip))
            req = requests.get(url, timeout=5)
            logging.info("此ip：{}访问正常".format(ip))
            flag = True
        except:
            url="http://"+ip+":8899"
            try:
                req = requests.get(url, timeout=5)
                logging.info("此ip：{}被假墙".format(ip))
            except:
                logging.info("此ip：{}访问异常，请手动检查".format(ip))
            flag = False
    return flag
def execute(domain,token,dianxiniplist,yidongiplist):
    api="https://dnsapi.cn/Record.List"
    data = {
        "login_token": token,
        "domain": domain,
        "format": "json"
    }
    req=requests.post(api,data=data,timeout=5)
    out_json=req.json()
    code=out_json["status"]["code"]
    if code=="1":
        records=out_json["records"]
        logging.info("获取正常的ip，请稍后！！！")
        #获取未被墙的ip用于修改a记录
        dianxinip=get_ip(dianxiniplist)
        yidongip=get_ip(yidongiplist)
        logging.info("获取到的正常电信IP：{}，移动IP：{}，进行替换".format(dianxinip,yidongip))
        time.sleep(1.5)
        api = "https://dnsapi.cn/Record.Modify"
        for record in records:
            if record["type"]=="A":
                if record["line"]=="移动":
                    ip=yidongip
                elif record["line"]=="搜索":
                    continue
                else:
                    ip=dianxinip
                data = {
                    "login_token": token,
                    "domain": domain,
                    "record_id": record["id"],
                    "sub_domain":record["name"],
                    "record_type": "A",
                    "record_line": record["line"],
                    "value": ip,
                    "ttl":"120",
                    "format": "json"
                }
                req = requests.post(api, data=data, timeout=5)
                out_json = req.json()
                code = out_json["status"]["code"]
                if code == "1":
                    logging.info("完成域名：{}下A记录:{}的IP：{}的替换".format(domain,record["name"],ip))
                else:
                    logging.info("通过api修改域名记录：{}异常，请手动检查==={}".format(domain,req.text))
    else:
        logging.info("通过api查询域名：{}异常，请手动检查==={}".format(domain,req.text))
if __name__ == '__main__':
    getlogger()
    domain="xxxx.com"
    #通过dnspod获取密钥
    token="id,Token"
    oldip="23.11.11.15"
    dianxiniplist = get_ip_list("电信.txt")
    yidongiplist= get_ip_list("移动.txt")
    if len(dianxiniplist)==0 or len(yidongiplist)==0:
        logging.info("电信或移动文件里面未发现ip地址，脚本执行结束")
        exit()
    n=1
    while True:
        biaoji=if_ip_qiang2(oldip)
        if biaoji==False:
            n=n+1
            logging.info("原有ip可能被墙，过5s重试第{}次".format(oldip,str(n)))
            time.sleep(5)
        else:
            n=1
            logging.info("原有ip访问正常，继续执行".format(oldip))
            time.sleep(60)
        if n>3:
            logging.info("超过3次测试ip：{}都无法访问，被墙，执行以下脚本".format(oldip))
            break
    n = 1
    while True:
        execute(domain,token,dianxiniplist,yidongiplist)
        logging.info("当前执行完第{}次".format(str(n)))
        time.sleep(60*2)
        n=n+1