# 链家二手房爬虫
本程序基于Python3编写，可以爬取链家网所有成交的二手房的相关信息，并具有断点续传功能，可以随时中断爬取，下次运行程序时将从中断处继续
爬取数据，不会造成数据重复，数据存储使用mongodb。
# 所需库
以下所有安装命令基于ubuntu
* lxml  
`
sudo apt-get install python3-lxml
`
* BeautifulSoup4  
`
pip3 install beautifulsoup4
`
* Requests  
`
pip3 install requests
`
* Pymongo  
`
pip3 install pymongo
`
# 使用
* 爬虫程序默认设置为爬取大连链家网的信息，可以通过查找替换将程序中的``dl.lianjia.com``替换为所要爬取的地区的网址
，例如要爬取北京的二手房成交信息则替换为``bj.lianjia.com``。同时需要将程序中headers中的cookie信息替换为自己浏览器的信息，你可以通过F12
获取相关的信息。  
![f12](https://cl.ly/3l201i3J3O2i/Desctop%20screenshot.png)
* 修改完成后打开终端，进入爬虫程序所在目录，然后执行文件即可``python3 chengjiao_ershoufang.py``。
# 交流讨论
如果有任何问题或者对程序有更好的改进的想法，可以通过邮箱联系我``gostmr@foxmail.com``。


