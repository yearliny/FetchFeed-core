# -*- coding:utf-8 -*-
import os
import re
import sys
import time
import hashlib
import requests


class GetPage:
    def __init__(self, url, cache_path='cache', levels='1:2'):
        self.original_url = url
        if '}' in url[-1]:
            self.url = url[:url.find('{')]
            self.encoding = url[url.find('{')+1:-1]
        else:
            self.url = url
            self.encoding = None
        self.cache_path = cache_path
        self.levels = levels

    def _get_path(self):
        # 通过url生成hash值，按照levels计算生成路径
        if self.original_url != self.url:
            self.url = self.original_url
        url_hash = hashlib.md5(self.url.encode('utf-8')).hexdigest()
        path_list = []
        for i in (int(i) for i in self.levels.split(':')):
            path_list.append(url_hash[:i])
            url_hash = url_hash[i:]
        else:
            path_list.append(url_hash)
        file_path = os.path.join(sys.path[0], self.cache_path, *path_list)
        return file_path

    def get_html(self):
        # 通过requests获得网页源码，并返回
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'
        }
        result = {}
        try:
            page_html = requests.get(self.url, headers=headers, timeout=8)
            if page_html and self.encoding:
                page_html.encoding = self.encoding
            result['code'] = 0
            result['status'] = 'Effective URL is {}. ' \
                               'Page loaded successfully (encoding: {})'.format(page_html.url, page_html.encoding)
            result['response'] = page_html.text
        except requests.exceptions.HTTPError as e:
            result['code'] = 1
            result['status'] = 'HTTP Error:' + str(e)
            result['response'] = None
        except requests.exceptions.Timeout as e:
            result['code'] = 1
            result['status'] = 'TimeOut:' + str(e)
            result['response'] = None
        except requests.exceptions.ConnectionError as e:
            result['code'] = 1
            result['status'] = 'Connection Error:' + str(e)
            result['response'] = None
        except requests.exceptions.RequestException as e:
            result['code'] = 1
            result['status'] = 'OOps: Something Else:' + str(e)
            result['response'] = None
        return result

    def read(self, cache_time=4):
        # 先寻找url对应文件是否存在缓存并与当前时间相差小于4小时，否则就先请求网页并覆盖旧缓存，然后返回网页源码
        file_path = self._get_path()
        result = {}
        # 对应缓存文件是否存在
        if os.path.exists(file_path):
            if not time.time() - os.path.getmtime(file_path) > 60*60*cache_time:
                with open(file_path, 'r', encoding='utf-8') as html_file:
                    page_html = html_file.read()
                result['code'] = 0
                result['status'] = 'Page loaded successfully by cache.'
                result['response'] = page_html
            # 缓存过期时，更新本地缓存并返回数据
            else:
                page_html = self.get_html()
                result.update(page_html)
                with open(file_path, 'w+', encoding='utf-8') as html_file:
                    html_file.write(page_html['response'])
        # 没有缓存文件时，先获取网页，检查目录是否存在，然后写入并返回数据
        else:
            page_html = self.get_html()
            result.update(page_html)
            if page_html['code'] == 0:
                # 如果目录存在，则直接创建文件
                if os.path.exists(os.path.dirname(file_path)):
                    with open(file_path, 'w+', encoding='utf-8') as html_file:
                        html_file.write(page_html['response'])
                # 目录不存在，先创建目录然后更新缓存
                else:
                    os.makedirs(os.path.dirname(file_path))
                    page_html = self.get_html()
                    with open(file_path, 'w+', encoding='utf-8') as html_file:
                        html_file.write(page_html['response'])
        return result


class FeedMaker:
    # TODO: 自定义错误基类，当P元素或规则不合法时抛出异常，下游函数直接捕获错误而无须多重嵌套条件判断
    """Main class for making feeds. Contains methods for setting
    parameters, input parsing, and feed generation."""
    def __init__(self, page_file):
        self.page_file = page_file
        if page_file['response']:
            self.page = page_file['response']
        self.code = page_file['code']
        self.status = page_file['status']

    def _parse(self, pattern, max_items=-1):
        """Parse string according to pattern and return a list of items.
        Parsing stops when maxitems > 0 are found."""
        pieces = [p for p in re.split(r'({[*%]})', pattern) if p]
        assert pieces, 'There is no {%} in patterns.Please check the input and try again.'
        items = []
        begin = 0
        while begin < len(self.page) and len(items) != max_items:
            keep = False
            item = []
            for p in pieces:
                if p == '{*}':
                    keep = False
                elif p == '{%}':
                    keep = True
                else:
                    end = self.page.find(p, begin)
                    if end == -1:
                        break
                    if keep:
                        item.append(self.page[begin:end])
                    begin = end + len(p)
            else:
                if p == '{%}':
                    item.append(self.page[begin:])
                    begin = len(self.page)
            if not item:
                break
            items.append(item)
        assert items, 'Can not find any item, please check the input and try again'
        return items

    def extract(self, item_pattern,  global_pattern=None):
        # 获取self.page、item_pattern、global_pattern对象，返回一个字典，字典包含响应码、消息、和提取内容
        # 1.判断网页是否成功获取，获取失败则直接返回失败信息
        # 2.判断是否有全局规则，有全局规则先进行全局规则过滤
        # 3.判断 item_pattern 是否成功提取项目，若失败则报错。
        result = {'code': 0, 'response': {}}
        if self.code != 0:
            return self.page_file
        try:
            if not global_pattern:
                items = self._parse(item_pattern)
            else:
                # 先进行全局规则过滤，然后进行条目规则过滤
                items = self._parse(global_pattern, max_items=1)
                if items and items[0]:
                    # items[0][0] 是经过全局过滤后的第一条信息
                    items = self._parse(items[0][0], item_pattern)
            result['status'] = 'OK ({} items found)'.format(len(items))
        except AssertionError as e:
            result['code'] = 1
            result['status'] = e

        for index, item in enumerate(items, start=1):
            current_item = {'item'+str(index): item}
            result['response'].update(current_item)
        return result


if __name__ == '__main__':
    page = GetPage("https://yuan.ga").read()
    print(FeedMaker(page).extract('<h3 class="entry-title"><a href="{%}" rel="bookmark">{%}</a></h3>'))

