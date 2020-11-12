import os
import sys
import shutil
import json
import random
from threading import Thread
from EulerInit.Convertor.BaseConvertor import BaseConvertor
from EulerInit.Convertor.tool.downloader import Downloader
from EulerInit.Convertor.tool.iso import ReaderISO
from EulerInit.Convertor.tool.fileServer import ModelServer
from EulerInit.Convertor.tool.qemu import Controller


class Convertor(BaseConvertor):
    def __init__(self):
        self.template = ''
        self.cfg = None
        self.iso = ''
        self.outputPath = ''
        self.offline = False
        self.system = ''
        self.size = ''
        self.passwd = ''
        self.platform = ''
        self.server = None
        self.controller = None
        self.callbacks = None
        self.tmpFileName = ''
        self.version = ''
        self.kernelRawArgs = None

    def setup(self, isoPath: str, template: str, system: str, size: str,
              passwd: str, version: str, outputPath: str = None, callbacks: dict = None):
        """
        设置相关参数
        :param isoPath: ISO镜像文件路径
        :param template: 模板文件夹路径
        :param system: 所安装镜像平台，x86_64或aarch64
        :param size: 所安装镜像大小
        :param passwd: 所安装镜像密码
        :param version: 所安装镜像版本
        :param outputPath: 镜像输出文件夹
        :param callbacks: 回调函数字典
        :return: NULL
        """
        self.template = template
        # 用户指定
        self.iso = os.path.abspath(isoPath)
        self.outputPath = os.path.join(os.getcwd(), 'tmp') if not outputPath else outputPath
        self.system = system
        self.size = size
        self.passwd = passwd
        self.version = version
        self.callbacks = callbacks
        # 自动识别
        self.platform = sys.platform
        # 自动生成
        self.tmpFileName = 'virtual_{:d}.img'.format(random.randint(0, 100000))

        if self.callbacks:
            self.callbacks['echo']("[step 1/6] : setup basic arguments...")
        if self.callbacks:
            self.callbacks['echo']("-> Done")

    # 准备安装所需文件
    def prepare(self):
        """
        准备安装所需文件,一般可能来源：
        1. 下载(可以使用tool/downloader中的相关工具)
        2. 从ISO文件中抽取(可以使用tool/iso中的相关工具)
        3. 在模板文件中指定
        :return: NULL
        """
        if self.callbacks:
            self.callbacks['echo']("[step 2/6] : Preparing files for install...")
        # 模板文件夹内容拷贝到输出文件夹
        if self.callbacks:
            self.callbacks['echo']("-> Copying from template")
        shutil.copytree(self.template, self.outputPath, dirs_exist_ok=True)

        # 从输出文件夹读取files.cfg获得下载文件列表
        if self.callbacks:
            self.callbacks['echo']("-> Reading download config(files.json)")
        with open(os.path.join(self.outputPath, 'files.json'), 'r') as f:
            self.cfg = json.load(f)

        # 下载相关文件
        if self.callbacks:
            self.callbacks['echo']("-> Download begin")
        downloader = Downloader()
        for file, url in self.cfg[self.system]['download'].items():
            if os.path.exists(os.path.join(self.outputPath, self.cfg[self.system]['file'][file])):
                if self.callbacks:
                    self.callbacks['echo']("  - {file} exist".format(file=self.cfg[self.system]['file'][file]))
                continue
            finished = False
            times = 0
            while not finished and times <= 3:
                times += 1
                if self.callbacks:
                    self.callbacks['echo']("  - {file} download...".format(file=self.cfg[self.system]['file'][file]))
                    finished = downloader.download(url,
                                                   os.path.join(self.outputPath, self.cfg[self.system]['file'][file]),
                                                   self.callbacks['progressbar'])
                else:
                    finished = downloader.download(url,
                                                   os.path.join(self.outputPath, self.cfg[self.system]['file'][file]))
            if not finished:
                raise Exception("Downloaded: reach max tried")

        # 从ISO镜像文件抽取出相关内核文件
        if self.callbacks:
            self.callbacks['echo']("-> Extracting kernel from ISO")
        reader = ReaderISO(self.iso, self.outputPath)
        fetchRoutes = ('/images/pxeboot/vmlinuz', '/images/pxeboot/initrd.img', '/EFI/BOOT/grub.cfg')
        reader.extract(fetchRoutes)

        # 从grub.cfg中获得原始内核参数
        with open(os.path.join(self.outputPath, 'grub.cfg'), 'r') as f:
            lines = f.readlines()
        prefix = ['linuxefi', 'linux'][['x86_64', 'aarch64'].index(self.system)]
        for line in lines:
            line = line.strip().rstrip()
            if line.startswith('{prefix} /images/pxeboot/vmlinuz'.format(prefix=prefix)):
                line = line[len('{prefix} /images/pxeboot/vmlinuz'.format(prefix=prefix)):].strip()
                # 删去aarch64中可能的终端重定向
                start = line.find('console=tty0')
                if start != -1:
                    end = start + len('console=tty0')
                    line = line[:start] + line[end:]
                self.kernelRawArgs = line
                break

        if self.callbacks:
            self.callbacks['echo']("-> Done")

    # 在输出文件夹位置启动文件服务器
    def serverUp(self):
        """
        启动文件服务器，为避免阻塞需要使用新开线程/进程(可以使用tool/fileServer中的相关工具)
        :return: NULL
        """
        if self.callbacks:
            self.callbacks['echo']("[step 3/6] : Setting up file server...")
        # 符号替换列表
        subDict = {
            'is_x86_64_pound': '#' if self.system == 'x86_64' else '',
            'is_aarch64_pound': '#' if self.system == 'aarch64' else '',
            'passwd': self.passwd,
            'version': self.version
        }
        self.server = ModelServer(self.outputPath, subDict)
        server_thread = Thread(target=self.server.serve_forever, name='server')
        server_thread.start()
        if self.callbacks:
            self.callbacks['echo']("-> Done")

    # 执行QEMU安装流程(分配空间和实际安装)
    def install(self):
        """
        执行QEMU安装流程(可以使用tool/qemu中的相关工具):
        1. 分配空间
        2. 实际安装
        :return: NULL
        """
        # 格式化配置
        if self.callbacks:
            self.callbacks['echo']("[step 4/6] : Starting QEMU img install...")
        # 符号替换列表
        subDict = {
            'system': self.system,
            'img_path': os.path.join(self.outputPath, self.tmpFileName),
            'iso_path': self.iso,
            'machine': 'pc' if self.system == 'x86_64' else 'virt',
            'vmlinuz_path': os.path.join(self.outputPath, 'vmlinuz'),
            'initrd_path': os.path.join(self.outputPath, 'initrd.img'),
            'bios_path': os.path.join(self.outputPath, 'QEMU_EFI.fd'),
            'kernel_args': self.kernelRawArgs
        }
        self.controller = Controller(self.outputPath, self.iso)
        self.controller.create(self.size, self.tmpFileName)
        self.controller.install(subDict)
        if self.callbacks:
            self.callbacks['echo']("-> Done")

    # 关闭文件服务器
    def serverDown(self):
        """
        关闭文件服务器
        :return: NULL
        """
        if self.callbacks:
            self.callbacks['echo']("[step 5/6] : shutdown the file server...")
        self.server.shutdown()
        self.callbacks['echo']("-> Done")

    # 格式转换
    def output(self, img: str, format: str):
        """
        执行镜像生成后续工作，如格式转换或重命名
        :param img: 导出镜像文件名
        :param format: 导出镜像格式
        :return:
        """
        if self.callbacks:
            self.callbacks['echo']("[step 5/6] : Output the img file...")
        self.controller.convert(self.tmpFileName, img, format)
        os.remove(os.path.join(self.outputPath, self.tmpFileName))
        if self.callbacks:
            self.callbacks['echo']("-> Done")
