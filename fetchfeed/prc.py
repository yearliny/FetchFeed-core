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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) /'
            'Chrome/62.0.3202.94 Safari/537.36'
        }
        try:
            page_html = requests.get(self.url, headers=headers, timeout=8)
        except requests.exceptions.HTTPError as e:
            print('HTTP Error:', e)
        except requests.exceptions.Timeout as e:
            print('TimeOut:', e)
        except requests.exceptions.ConnectionError as e:
            print('Connection Error：', e)
        if page_html and self.encoding:
            page_html.encoding = self.encoding
        return page_html.text

    def read(self, cache_time=4):
        # 先寻找url对应文件是否存在缓存并与当前时间相差小于4小时，否则就先请求网页并覆盖旧缓存，然后返回网页源码
        file_path = self._get_path()
        if os.path.exists(file_path):
            if time.time() - os.path.getmtime(file_path) > 60*60*cache_time:
                page_html = self.get_html()
                with open(file_path, 'w+') as html_file:
                    html_file.write(page_html)
            else:
                with open(file_path, 'r') as html_file:
                    page_html = html_file.read()
            return page_html
        elif os.path.exists(os.path.dirname(file_path)):
            page_html = self.get_html()
            with open(file_path, 'w+') as html_file:
                html_file.write(page_html)
            return page_html
        else:
            os.makedirs(os.path.dirname(file_path))
            page_html = self.get_html()
            with open(file_path, "w+") as html_file:
                html_file.write(page_html)
            return page_html


class FeedMaker:
    """Main class for making feeds. Contains methods for setting
    parameters, input parsing, and feed generation."""
    def __init__(self, page_file):
        self.items = []
        self.page = page_file

    def _parse(self, pattern, max_items=-1):
        """Parse string according to pattern and return a list of items.
        Parsing stops when maxitems > 0 are found."""
        items = []
        pieces = [p for p in re.split(r'({[*%]})', pattern) if p]
        begin = 0
        while p and begin < len(self.page) and len(items) != max_items:
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
        return items

    def extract(self, item_pattern,  global_pattern=None):
        if not global_pattern:
            self.items.extend(self._parse(item_pattern))
        else:
            items = self._parse(global_pattern, max_items=1)
            if items and items[0]:
                # items[0][0] 是经过全局过滤后的第一条信息
                self.items.extend(self._parse(items[0][0], item_pattern))
            else:
                print("无法匹配到任何条目")
        result = []
        item_num = 1
        for item in self.items:
            current_item = {'item'+str(item_num): item}
            item_num += 1
            result.append(current_item)
        return result

    def expand(self, item_prop):
        result = []
        for piece in re.split(r'{(\w)+}', item_prop):
            m = re.match(r'{(\w)+}', piece)
            if m:
                m = int(m.group(1)) - 1
                for i in self.items:
                    result.append(i[m])
            else:
                result.append(piece)
        return ''.join(result)


if __name__ == '__main__':
    page = GetPage("https://www.baidu.com").read()
    print(page)
