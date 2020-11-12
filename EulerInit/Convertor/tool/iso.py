try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

import pycdlib
import os


class ReaderISO:
    """
    ISO文件读取工具类
    """
    def __init__(self, iso_path: str, out_path: str = None):
        """
        初始化工具类
        :param iso_path: 待处理的ISO文件路径
        :param out_path: 输出文件夹路径
        """
        self.iso_path = iso_path
        self.out_path = os.getcwd() if not out_path else out_path

    def extract(self, fetch_routes: tuple):
        """
        :param fetch_routes: 从ISO文件中抽取的文件路径集合
        :return: NULL
        """
        iso = pycdlib.PyCdlib()
        iso.open(self.iso_path)
        for route in fetch_routes:
            filename = route.split('/')[-1]
            extracted = open(os.path.join(self.out_path, filename), 'wb')
            iso.get_file_from_iso_fp(extracted, joliet_path=route)
            extracted.close()
        iso.close()

