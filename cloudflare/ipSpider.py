#http://103.21.244.236/cdn-cgi/trace
import time
import requests
import ipaddress
from multiprocessing.pool import ThreadPool
import threading
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
def ping_host(ip,tmp_ip_dict,tmpfile,lock):
    result=tmp_ip_dict.__contains__(ip)
    if result:
        latency=tmp_ip_dict[ip][1]
        loss=tmp_ip_dict[ip][2]
        if latency < 200 and loss == 0:
            logging.info("缓存，IP：{}，延迟：{}，丢包：{}满足条件，存入".format(ip, str(latency), str(loss)))
            tmp_ip_list.append(result)
        else:
            logging.info("缓存，IP：{}，延迟：{}，丢包：{}不满足条件，忽略".format(ip, str(latency), str(loss)))
    else:
        popen = subprocess.Popen('ping -w 1 %s' %ip, stdout=subprocess.PIPE,shell=True)
        popen.wait()
        res = popen.stdout.read().decode('gbk').strip('\n')
        if "平均" in res:
            try:
                latency = re.findall("平均 = \d+ms", res)[0]
                latency = re.findall(r"\d+", latency)[0]
                loss = re.findall("\d+% 丢失", res)[0]
                loss = re.findall(r"\d+", loss)[0]
                if int(latency) < 200 and int(loss) == 0:
                    logging.info("IP：{}，延迟：{}，丢包：{}满足条件，存入".format(ip,latency,loss))
                    tmp_ip_list.append((ip, int(latency), int(loss)))
                else:
                    logging.info("IP：{}，延迟：{}，丢包：{}不满足条件，忽略".format(ip, latency, loss))
                #存入临时缓存文件,加锁
                lock.acquire()  # 加锁
                tmpfile.write(str((ip, int(latency), int(loss)))+"\n")
                tmpfile.flush()
                lock.release()
            except Exception as e:
                print(e)
def get_all_ips(hosts):
    ips = []
    net4 = ipaddress.ip_network(hosts.strip())
    n=1
    for host in net4.hosts():
        if n==1:
            n=n+1
            continue
        ips.append(str(host))
        n=n+1
    logging.info("IP段：{}共获取到{}个IP，稍后进行ping延迟和丢包测试".format(hosts.strip(),str(len(ips))))
    time.sleep(1.5)
    return ips
def http_Test(ipinfo):
    global ipresult
    ip=ipinfo[0]
    api="http://{}/cdn-cgi/trace".format(ip)
    req=requests.get(api,timeout=3)
    if ip in req.text:
        colo=re.search("colo=(.*?)\n",req.text).group(1)
        logging.info("IP:{}，HTTP测试正常,区域：{}，存入数据库".format(ip,colo))
        ipresult.append(ipinfo+(colo,))
    else:
        logging.info("IP:{}，HTTP测试失败，IP被墙或者有问题，忽略".format(ip))
def start(threadnum):
    global ipresult
    global tmp_ip_list
    logging.info("----开始本次cloudflare的IP采集----")
    #读缓存文件
    tmp_ip_dict={}
    file_size=os.path.getsize("tmpip.txt")
    if file_size!=0:
        with open("tmpip.txt", "r") as file:
            for each in file.readlines():
                host=each.strip()
                if "." in host:
                    host = tuple(eval(host))
                    tmp_ip_dict[host[0]]=host
            logging.info("读取缓存文件，共获取到{}个临时IP数据".format(str(len(tmp_ip_dict))))
            time.sleep(1.5)
    with open("cloudflare.txt", "r") as f1,open("over.txt", "a") as f2,open("over.txt", "r") as f3:
        overlines=f3.readlines()
        for hosts in f1.readlines():
            flag=False
            for each in overlines:
                if hosts.strip() in each:
                    flag=True
                    break
            if flag==True:
                logging.info("IP段：{}已采集过，略过".format(hosts.strip()))
                continue
            ips=get_all_ips(hosts.strip())
            with open("tmpip.txt", "a") as tmpfile:
                # 线程数，可自行调整
                pool = ThreadPool(int(threadnum))
                lock = threading.Lock()
                for ip in ips:
                    pool.apply_async(ping_host, args=(ip,tmp_ip_dict,tmpfile,lock))
                pool.close()
                pool.join()
                #写入缓存文件
                logging.info("IP段：{}共采集到{}个临时IP数据满足丢包和延迟，将要进行HTTP验证判断IP是否被墙".format(hosts.strip(), str(len(tmp_ip_list))))
                time.sleep(1.5)
                ipresult=[]
                pool = ThreadPool(20)
                for ipinfo in tmp_ip_list:
                    pool.apply_async(http_Test, args=(ipinfo,))
                pool.close()
                pool.join()
                logging.info("IP段：{}完成HTTP验证判断IP是否被墙测试".format(hosts.strip()))
                time.sleep(1.5)
            if len(ipresult)>0:
                logging.info("完成IP段：{}采集，共有{}个IP满足，写入临时文件".format(hosts.strip(), str(len(ipresult))))
                time.sleep(1.5)
                with open("tmpresult.txt", "a") as f:
                    for each in ipresult:
                        f.write(str(each)+"\n")
            else:
                logging.info("完成IP段：{}采集，未采集到满足条件的IP".format(hosts.strip()))
                time.sleep(1.5)
            logging.info("清空IP段：{}相关的临时数据".format(hosts.strip()))
            time.sleep(1.5)
            with open("tmpip.txt", "w") as f:
                f.seek(0)
                f.truncate()
            tmp_ip_dict={}
            tmp_ip_list=[]
            #设置ip段为已采集
            f2.write(hosts.strip()+":ok"+"\n")
            f2.flush()
    #按照ping延迟低到高进行排序
    logging.info("按照IP ping延迟低到高进行排序")
    iplist = []
    with open("tmpresult.txt", "r") as f, open("ip.txt", "w") as f2:
        for line in f.readlines():
            iplist.append(tuple(eval(line.strip())))
        iplist.sort(key=takeSecond)
        for each in iplist:
            f2.write(str(each) + "\n")
    #清空临时文件
    with open("tmpresult.txt", "w") as f:
        f.seek(0)
        f.truncate()
    logging.info("----完成本次cloudflare的IP采集----")
if __name__ == '__main__':
    getlogger()
    start(100)