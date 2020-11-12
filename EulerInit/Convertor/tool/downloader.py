import os
import re
import requests


class Downloader:
    """
    文件下载管理器
    """
    def __init__(self):
        self.total = 0
        self.size = 0
        self.filename = ''

    def _down_once(self, chunk: bytes, size: int, f):
        """
        执行单次块写入，内部使用
        :param chunk: 块内容
        :param size: 写入前文件总大小
        :param f: 文件写指针
        :return: size: 写入后文件总大小
        """
        if chunk:
            f.write(chunk)
            size += len(chunk)
        return size

    def download(self, url: str, filename: str = None, progressbar=None):
        """
        进行文件下载
        :param url: 下载地址
        :param filename: 保存文件名
        :param progressbar: 进度条对象(click.progressbar)
        :return:
        """
        headers = {}
        finished = False
        block = 1024
        localFilename = url.split('/')[-1] if not filename else filename
        tmpFilename = localFilename + '.downtmp'
        size = self.size
        if self.supportCont(url):
            try:
                with open(tmpFilename, 'rb') as fin:
                    self.size = int(fin.read())
                    size = self.size + 1
            except:
                self.touch(tmpFilename)
            finally:
                headers['Range'] = "bytes={:d}-".format(self.size)
        else:
            self.touch(tmpFilename)
            self.touch(localFilename)

        total = self.total
        r = requests.get(url, stream=True, verify=True, headers=headers)
        if total == 0:
            total = size
        with open(localFilename, 'ab+') as f:
            f.seek(self.size)
            f.truncate()
            try:
                if not progressbar:
                    for chunk in r.iter_content(chunk_size=block):
                        size = self._down_once(chunk, size, f)
                else:
                    with progressbar(length=total, label='Downloading') as bar:
                        for chunk in r.iter_content(chunk_size=block):
                            size = self._down_once(chunk, size, f)
                            bar.update(len(chunk))
                finished = True
                os.remove(tmpFilename)
            except Exception as e:
                print(e)
                finished = False
            finally:
                if not finished:
                    with open(tmpFilename, 'wb') as ftmp:
                        ftmp.write(str(size).encode('utf-8'))
                return finished

    def supportCont(self, url: str):
        """
        验证是否支持断线重连
        :param url: 下载地址
        :return: success: 是否支持断线重连
        """
        headers = {
            'Range': 'bytes=0-4'
        }
        try:
            r = requests.head(url, headers=headers)
            crange = r.headers['content-range']
            self.total = int(re.match(r'^bytes 0-4/(\d+)$', crange).group(1))
            return True
        except:
            pass
        try:
            self.total = int(r.headers['content-length'])
        except:
            self.total = 0
        return False

    def touch(self, filename: str):
        """
        截断文件
        :param filename: 文件名
        :return: NULL
        """
        with open(filename, 'w') as fin:
            fin.truncate()
