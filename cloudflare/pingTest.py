#http://103.21.244.236/cdn-cgi/trace
import time
import requests
from multiprocessing.pool import ThreadPool
import subprocess
import re
import logging  # 引入logging模块
import os
tmp_ip_list=[]
ipresult=[]
def getlogger():
    # 第一步，创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关
    # 第二步，创建一个handler，用于写入日志文件
    rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    log_path = os.getcwd() + '/Logs/'
    log_name = log_path + rq + '.log'
    logfile = log_name
    fh = logging.FileHandler(logfile, encoding='utf-8')
    fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # 输出到console的log等级的开关
    # 第三步，定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # 第四步，将logger添加到handler里面
    logger.addHandler(fh)
    logger.addHandler(ch)
#按照第二个元素进行排序
def takeSecond(elem):
    return elem[1]
def ping_host(ip):
    popen = subprocess.Popen('ping -w 1 %s' %ip, stdout=subprocess.PIPE,shell=True)
    popen.wait()
    res = popen.stdout.read().decode('gbk').strip('\n')
    if "平均" in res:
        try:
            latency = re.findall("平均 = \d+ms", res)[0]
            latency = re.findall(r"\d+", latency)[0]
            loss = re.findall("\d+% 丢失", res)[0]
            loss = re.findall(r"\d+", loss)[0]
            if int(latency)<200 and int(loss)==0:
                logging.info("IP：{}，延迟：{}，丢包：{}满足条件,存入".format(ip,latency,loss))
                tmp_ip_list.append((ip, int(latency), int(loss)))
            else:
                logging.info("IP：{}，延迟：{}，丢包：{}不满足条件，忽略".format(ip, latency, loss))
        except Exception as e:
            print(e)
def get_ip_list():
    iplist=[]
    with open("ip.txt","r") as f:
        for line in f.readlines():
            iplist.append(tuple(eval(line.strip()))[0])
    logging.info("从ip.txt文件中获取到{}个IP，将要进行ping延迟和丢包率测试".format(str(len(iplist))))
    time.sleep(1.5)
    return iplist


def http_Test(outcome):
    global ipresult
    ip=outcome[0]
    api="http://{}/cdn-cgi/trace".format(ip)
    req=requests.get(api,timeout=3)
    if ip in req.text:
        colo=re.search("colo=(.*?)\n",req.text).group(1)
        logging.info("IP:{}，HTTP测试正常,区域：{}，存入数据库".format(ip, colo))
        ipresult.append(outcome+(colo,))
    else:
        logging.info("IP:{}，HTTP测试失败，IP被墙或者有问题，忽略".format(ip))
def start(threadnum):
    global ipresult
    global tmp_ip_list
    logging.info("----开始本次的IP采集,线程个数：{}----".format(str(threadnum)))
    with open("tmpresult.txt","w") as f:
        ips=get_ip_list()
        # 线程数，可自行调整
        pool = ThreadPool(int(threadnum))
        for ip in ips:
            pool.apply_async(ping_host, args=(ip,))
        pool.close()
        pool.join()
        #写入缓存文件
        logging.info("共采集到{}个临时IP数据满足丢包和延迟，将要进行HTTP验证判断IP是否被墙".format(str(len(tmp_ip_list))))
        time.sleep(1.5)
        pool = ThreadPool(20)
        for ipinfo in tmp_ip_list:
            pool.apply_async(http_Test, args=(ipinfo,))
        pool.close()
        pool.join()
        logging.info("完成HTTP验证判断IP是否被墙测试")
        time.sleep(1.5)
        if len(ipresult)>0:
            logging.info("共有{}个IP满足，写入临时文件".format(str(len(ipresult))))
            time.sleep(1.5)
            for each in ipresult:
                f.write(str(each)+"\n")
        else:
            logging.info("未采集到满足条件的IP")
            time.sleep(1.5)
    # 按照ping延迟低到高进行排序
    logging.info("将要按照IP ping延迟低到高进行排序")
    time.sleep(1.5)
    iplist = []
    with open("tmpresult.txt", "r") as f, open("ip.txt", "w") as f2:
        for line in f.readlines():
            iplist.append(tuple(eval(line.strip())))
        iplist.sort(key=takeSecond)
        for each in iplist:
            f2.write(str(each) + "\n")
    logging.info("完成按照IP ping延迟低到高进行排序")
    time.sleep(1.5)
    print("完成本次ip ping测试")
if __name__ == '__main__':
    getlogger()
    start(100)

