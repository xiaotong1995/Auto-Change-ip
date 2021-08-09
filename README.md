# Auto-Change-ip
## cf yes  (搬运HostLoc 脆弱的蜗牛 )  REC

1、利用cloudflare的cname解析（cdn。wzfou。com）；

2、购买dnspod个人专业版，因为免费版600秒ttl，专业版可以最低120秒ttl，频繁改ip，ttl得低一点，重点：必须添加电信、移动、联通这三个线路的a记录；

3、cloudflare文件夹下先执行ipSpider.py抓取ip，然后pingTest.py在执行一遍，最终文件ip.txt（cloudflare的移动线路选择香港直连线路，所以你得想办法弄到2份ip.txt,或者移动直接用电信、联通的ip，但是不能电信、联通用移动的香港ip，因为绕了）。

4、dnspod里面先获取替换dnspod文件夹下dnshandle.py里面的token=id,Token，然后写上自己的域名即可；

5、懂点脚本的自己看着改下即可，小弟刚学python不久，脚本有不完善之处还请大神高抬贵手给指点一下，小弟来学习和完善；

6、cloudflare目录下面的电信.txt和移动.txt是我过滤好的，你可以直接拿来用，用pingTest.py在过滤一下，然后获取前1000个ip放在文件夹dnspod下面即可；

7、经测试电信和移动用户访问还是很快的，不比现在我的gia慢；

8、安装好python后只需要pip install requests安装这一个库即可；


cloudflare脚本的特点：

1、ipSpider.py扫描cloudflare所有开放的ip段，获取ping低于200ms和0丢包的ip，然后按照ping值从小到大写入到ip.txt；

2、pingTest.py对生成的ip.txt在进行一遍过滤，再生成ip.txt;

3、对于cloudflare被墙的ip进行了过滤；

