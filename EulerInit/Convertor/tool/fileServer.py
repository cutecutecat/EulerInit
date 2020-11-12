from http.server import BaseHTTPRequestHandler, HTTPServer
import os


class ModelHandler(BaseHTTPRequestHandler):
    """
    本地文件服务器
    """
    fileDirPath = os.getcwd()
    subDict = {}

    @classmethod
    def model(cls, buf: bytes):
        """
        执行符号替换
        :param buf: 原始字符串
        :return:
        """
        sbuf = str(buf, encoding="utf8")
        sbuf = sbuf.format(**cls.subDict)
        buf = bytes(sbuf, encoding="utf8")
        return buf

    def do_GET(self):
        """
        服务器的GET方法，提供文本信息
        :return: NULL
        """
        url = self.path
        filename = url.split('/')[-1]
        filepath = os.path.join(self.fileDirPath, filename)
        try:
            result = open(filepath, 'rb')
        except BaseException:
            self.send_response(404)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            buf = result.read()
            if filename == 'ks.cfg':
                buf = self.model(buf)
            self.wfile.write(buf)
            result.close()


def ModelServer(fileDirPath: str, subDict: dict, port: int = 8000):
    """
    :param fileDirPath: 服务器映射的实际文件夹
    :param subDict: 符号替换列表
    :param port: 服务器所在端口
    :return: 文件服务器对象
    """
    host = ('', port)
    ModelHandler.fileDirPath = fileDirPath
    ModelHandler.subDict = subDict
    server = HTTPServer(host, ModelHandler)
    return server

