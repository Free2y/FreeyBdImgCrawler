# -*- coding:utf-8 -*-
import argparse
import json
import os
import re
import socket
import sys
import time
import urllib
from multiprocessing import Pool

import BaiduTranslate


class FreeyBdImgCrawler:
    imgs_needs = 800
    time_sleep = 0.05
    per_page = 30
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

    def __init__(self, t=0.05):
        self.time_sleep = t

    '''
    zh    中文
    en    英语
    yue    粤语
    wyw    文言文
    jp    日语
    kor    韩语
    fra    法语
    spa    西班牙语
    th    泰语
    ara    阿拉伯语
    ru    俄语
    pt    葡萄牙语
    de    德语
    it    意大利语
    el    希腊语
    nl    荷兰语
    pl    波兰语
    bul    保加利亚语
    est    爱沙尼亚语
    dan    丹麦语
    fin    芬兰语
    cs    捷克语
    rom    罗马尼亚语
    slo    斯洛文尼亚语
    swe    瑞典语
    hu    匈牙利语
    cht    繁体中文
    vie    越南语
    '''

    def translate(self, word, dst, src):
        bdtD = BaiduTranslate.Dict()
        json = bdtD.dictionary(word, dst=dst, src=src)
        result = json['trans_result']['data'][0]['dst']
        return result

    def mkdir(self, path):
        import os
        path = path.strip()
        path = path.rstrip('\\')
        isExists = os.path.exists(path)

        if not isExists:
            os.makedirs(path)
            print(path + '创建成功')
            return True
        else:
            print(path + '目录已存在')
            return False

    def get_suffix(self, name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    # 保存图片
    def save_image(self, rsp_data, word, img_path):
        files_details = self.get_file_count(img_path, '.jpg')
        counter = files_details['counts'] + 1
        for image_info in rsp_data['data']:
            try:
                if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                    continue
                obj_url = image_info['replaceUrl'][0]['ObjUrl']
                thumb_url = image_info['thumbURL']
                url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (
                    urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                time.sleep(self.time_sleep)
                suffix = self.get_suffix(obj_url)
                # 指定UA和referrer，减少403
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    ('User-agent',
                     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'),
                ]
                urllib.request.install_opener(opener)
                # 保存图片
                filepath = img_path + '/%s' % (word[1] + str(counter) + str(suffix))
                urllib.request.urlretrieve(url, filepath)
                if os.path.getsize(filepath) < 5:
                    print("下载到了空文件，跳过!")
                    os.unlink(filepath)
                    continue
            except urllib.error.HTTPError as urllib_err:
                print(urllib_err)
                continue
            except Exception as err:
                time.sleep(1)
                print(err)
                print("产生未知错误，放弃保存")
                continue
            else:
                print(word[0] + "图+1,已有" + str(counter) + "张" + str(suffix) + "图")
                if counter >= self.imgs_needs:
                    break
                counter += 1

        return

    def get_data(self, word, pn, img_path):
        search = urllib.parse.quote(word[0])
        url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
            search, search, str(pn), self.per_page)
        # 设置header防403
        try:
            time.sleep(self.time_sleep)
            req = urllib.request.Request(url=url, headers=self.headers)
            page = urllib.request.urlopen(req)
            rsp = page.read()
        except UnicodeDecodeError as e:
            print(e)
            print('-----UnicodeDecodeErrorurl:', url)
        except urllib.error.URLError as e:
            print(e)
            print("-----urlErrorurl:", url)
        except socket.timeout as e:
            print(e)
            print("-----socket timout:", url)
        else:
            # 解析json
            # print(type(rsp))
            # print(rsp)
            # rsp = rsp.decode('utf-8','replace')
            # print(rsp)
            rsp_data = json.loads(rsp,strict=False)
            self.save_image(rsp_data, word, img_path)
        finally:
            page.close()

    def get_file_count(self, path, type):
        import os.path
        dir = path
        m = 0
        files = []
        for parentdir, dirname, filenames in os.walk(dir):
            for filename in filenames:
                files.append(filename)
                if os.path.splitext(filename)[1] == type:
                    m = m + 1
        return {'counts': m, 'filenames': files}

    def get_needs_imgs(self, img_type):
        tran_img_type = str(self.translate(img_type, 'en', 'zh')).lower()
        word = [img_type, tran_img_type]
        img_path = 'imgs/' + tran_img_type
        self.mkdir(img_path)

        img_pg = 0
        while True:
            files_details = self.get_file_count(img_path, '.jpg')
            count = files_details['counts']
            if count >= self.imgs_needs:
                print('{}指定文件夹下已经有{}张{}图片了'.format(str(img_type), str(self.imgs_needs), ".jpg"))
                break
            self.get_data(word, img_pg, img_path)
            img_pg += self.per_page

    def start(self, img_types=['手机'], total_num=80, per_page=30):
        """
        爬虫入口
        :param word: 抓取的关键词
        :param total_num: 需要抓取数据总数
        :param per_page: 每页数量
        :return:
        """
        self.per_page = per_page
        self.imgs_needs = total_num
        pool = Pool()
        pool.map(self.get_needs_imgs, img_types)


if __name__ == '__main__':

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("-ws", "--words", type=str, help="抓取关键词", required=True)
        parser.add_argument("-tn", "--total_num", type=int, help="需要抓取的总数", required=True)
        parser.add_argument("-pp", "--per_page", type=int, help="每页大小",
                            choices=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], default=30, nargs='?')
        parser.add_argument("-d", "--delay", type=float, help="抓取延时（间隔）", default=0.05)
        args = parser.parse_args()

        crawler = FreeyBdImgCrawler(args.delay)
        crawler.start(args.words.split(','), args.total_num, args.per_page)
    else:
        img_types = ['杨幂', '邓超', '沈腾']
        crawler = FreeyBdImgCrawler()
        crawler.start()
