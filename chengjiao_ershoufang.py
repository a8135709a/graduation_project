import multiprocessing
import time
import re
from bs4 import BeautifulSoup
import requests
import pymongo


headers = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 \
    Safari/537.36',
    'Host': 'dl.lianjia.com',
    'Cookie': 'select_city=210200; all-lj=492291e11daf53bf34d39f84cc442d11; lianjia_uuid=f7b8efc9-5416-46d7-8ef0-cb37dcfd35db; _smt_uid=590ec972.43eeb903; lianjia_ssid=3b2c3594-105f-450e-8bfa-dbaf1e11aab2'
}

client = pymongo.MongoClient('localhost', 27017, connect=False)
lianJia = client['lianjia']
area_list = lianJia['area_list']
all_page_url = lianJia['all_page_url']
all_house_url = lianJia['all_house_url']
all_house_info = lianJia['all_house_info']

area_links = []


def get_url():
    url = 'https://dl.lianjia.com/chengjiao/'
    wb_data = requests.get(url, headers=headers)
    wb_data.encoding = 'utf-8'
    soup = BeautifulSoup(wb_data.text, 'lxml')
    area_link = soup.select('.position > dl > dd > div > div > a')
    for i in area_link:
        area_links.append('https://dl.lianjia.com{}'.format(i.get('href')))
    print(area_links)

all_area_links = []


def get_all_url():
    get_url()
    for i in area_links:  # 初步筛选，简单去掉重复地区，但无法去除7个大区
        wb_data = requests.get(i, headers=headers)
        wb_data.encoding = 'utf-8'
        soup = BeautifulSoup(wb_data.text, 'lxml')
        all_area_link = soup.select('.position > dl > dd > div > div > a')
        for a in all_area_link:
            if a.get('href') in all_area_links:
                pass
            else:
                all_area_links.append(a.get('href'))
    for a in all_area_links:  # 去除7个大区,并将去重后的数据存入数据库
        d_url = 'https://dl.lianjia.com{}'.format(a)
        if d_url in area_links:
            pass
        else:
            wb_data = requests.get(d_url, headers=headers)
            wb_data.encoding = 'utf-8'
            soup = BeautifulSoup(wb_data.text, 'lxml')
            # time.sleep(2)
            data = {
                'url': d_url,
                'area': list(map(lambda x: x.text, soup.select('.position > dl > dd > div > div > a.selected'))),
                'sum': soup.select('.resultDes.clear > div > span')[0].text,
                'where': a
            }
            area_list.insert_one(data)
            print(data)
    print('\n完成，请执行第二步\n')


def get_all_page_url():
    for i in area_list.find():
        wb_data = requests.get(i['url'], headers=headers)
        soup = BeautifulSoup(wb_data.text, 'lxml')
        page = soup.find_all('div', 'page-box house-lst-page-box')
        for num in page:
            d = re.sub('\D', '', re.search(r':.*?,', num.get('page-data'), re.DOTALL).group())
            for a in range(1, int(d)+1):
                url = 'http://dl.lianjia.com{}pg{}/'.format(i['where'], a)
                data = {
                    'url': url,
                    'father_url': i['url'],
                    'area': i['area']
                }
                all_page_url.insert_one(data)
                print(data)
    print('\n完成，请执行第三步\n')

page_db_url = [url['url'] for url in all_page_url.find()]
page_index_url = [url['father_url'] for url in all_house_url.find()]
x = set(page_db_url)
y = set(page_index_url)
page_rest_url = x-y

def get_all_house_url():
    for i in page_rest_url:
        wb_data = requests.get(i, headers=headers)
        soup = BeautifulSoup(wb_data.text, 'lxml')
        date = soup.select('.dealDate')
        link = soup.select('.info > .title > a')
        title = soup.select('.info > .title > a')
        if soup.select('title')[0].text == '414 Request-URI Too Large':
            print('请打开网页输入验证码，程序将在15秒后继续执行', i)
            time.sleep(15)
        elif soup.find('div', attrs={'class': 'icon-404 icon fl'}):
            print(i, '页面不存在')
        else:
            for d, l, t in zip(date, link, title):
                data = {
                    'url': l.get('href'),
                    'father_url': i,
                    'area': [area['area'] for area in all_page_url.find({'url': i})][0],
                    'dealDate': d.get_text(),   # 成交日期
                    'title': t.get_text()
                }
                print(data)
                all_house_url.insert_one(data)
    print('\n完成，请执行第四步\n')

house_db_url = [url['url'] for url in all_house_url.find()]
house_index_url = [url['url'] for url in all_house_info.find()]
x = set(house_db_url)
y = set(house_index_url)
house_rest_url = x-y


def get_house_info():
    for i in house_rest_url:
        wb_data = requests.get(i, headers=headers)
        soup = BeautifulSoup(wb_data.text, 'lxml')
        # time.sleep(2)
        if soup.select('title')[0].text == '414 Request-URI Too Large':
            print('请打开网页输入验证码，程序将在15秒后继续执行', i)
            time.sleep(15)
        elif soup.find('div', attrs={'class': 'icon-404 icon fl'}):
            print(i, '页面不存在')
        else:
            data = {
                'url': i,  # 链接
                'title': [title['title'] for title in all_house_url.find({'url': i})][0],  # 标题
                'area': [area['area'] for area in all_house_url.find({'url': i})][0],  # 区域
                'price': soup.select('.dealTotalPrice > i')[0].text,  # 价格
                'unitPrice': soup.select('.info.fr > .price > b')[0].text,  # 平米价
                'dealCycle': soup.select('.msg > span > label')[1].text,  # 成交周期
                'see': soup.select('.msg > span > label')[3].text,  # 带看（次）
                'follow': soup.select('.msg > span > label')[4].text,  # 关注（人）
                'browse': soup.select('.msg > span > label')[5].text,  # 浏览（次）
                'dealDate': [i['dealDate'] for i in all_house_url.find({'url':i})][0],
                'saleDate': re.sub(' ', '', re.sub('挂牌时间', '', soup.select('.transaction > div > ul > li')[2].text)),  # 挂牌时间
                'pattern': re.sub(' ', '', re.sub('房屋户型', '', soup.select('.base > .content > ul > li')[0].text)),  # 房屋户型
                'spaceSize': re.sub('㎡', '', re.sub(' ', '', re.sub('建筑面积', '', soup.select('.base > .content > ul > li')[2].text)))   # 建筑面积
            }
            print(data)
            all_house_info.insert_one(data)
    print('\n所有数据爬取成功！\n')
# get_house_info()


def main():
    print('请按步骤执行并注意屏幕输出的提示：\
    \n1.first step\n2.second step\n3.third step\n4.fourth step\n0.exit')
    a = input('输入你的选择(1、2、3、4、0)：')
    if a == '1':
        get_all_url()
        main()
    elif a == '2':
        get_all_page_url()
        main()
    elif a == '3':
        get_all_house_url()
        main()
    elif a == '4':
        get_house_info()
    elif a == '0':
        exit()
    else:
        print('error')
        exit()


if __name__ == '__main__':
    pool = multiprocessing.Pool()
    pool.apply_async(main())
    pool.close()
    pool.join()
# get_house_info()