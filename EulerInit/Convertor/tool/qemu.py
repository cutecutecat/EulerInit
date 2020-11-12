from subprocess import Popen
import sys
import os
import json


class Controller:
    """
    QEMU操作工具类
    """
    def __init__(self, outputPath: str, iso: str):
        """
        初始化工具类
        :param outputPath: 输出文件夹路径
        :param iso: ISO文件路径
        """
        self.outputPath = outputPath
        self.iso = iso
        with open(os.path.join(self.outputPath, 'qemu.json'), 'r') as f:
            self.cfg = json.load(f)

    def create(self, size: str, filename: str):
        """
        创建虚拟硬盘文件
        :param size: 文件大小
        :param size: 文件名
        :return: NULL
        """
        cmd_post = '.exe' if sys.platform == 'win32' else ''
        cmd = 'qemu-img{cmd_post} create -f raw {img_path} {size} -q'.format(
            cmd_post=cmd_post,
            img_path=os.path.join(self.outputPath, filename),
            size=size
        )
        print(cmd, end='\n\n')
        popen = Popen(shell=True, args=cmd)
        popen.wait()
        return popen

    def install(self, subDict: dict):
        """
        执行QEMU虚拟机安装
        :param subDict: 符号替换列表
        :return: NULL
        """
        cfg = dict(self.cfg[subDict['system']])
        cmdPost = '.exe' if sys.platform == 'win32' else ''
        cmd = 'qemu-system-{system}{cmd_post} '.format(system=subDict['system'], cmd_post=cmdPost)
        for key, value in cfg.items():
            if type(value) == list:
                for words in value:
                    subCmd = '-{key} "{words}" '.format(key=key, words=words)
                    subCmd = subCmd.format(**subDict)
                    cmd += subCmd
            else:
                subCmd = '-{key} "{words}" '.format(key=key, words=value)
                subCmd = subCmd.format(**subDict)
                cmd += subCmd
        cmd = cmd.rstrip()
        print(cmd, end='\n')
        popen = Popen(shell=True, args=cmd)
        popen.wait()
        return popen

    def convert(self, oldName: str, img: str, format: str):
        """
        运行镜像格式转换
        :param oldName: 旧镜像文件名
        :param img: 新镜像文件名
        :param format: 新镜像格式
        :return: NULL
        """
        cmd_post = '.exe' if sys.platform == 'win32' else ''
        cmd = 'qemu-img{cmd_post} convert -f raw -O {format} {img_path} {new_path}'.format(
            cmd_post=cmd_post,
            format=format,
            img_path=os.path.join(self.outputPath, oldName),
            new_path=os.path.join(self.outputPath, img)
        )
        print(cmd)
        popen = Popen(shell=True, args=cmd)
        popen.wait()
        return popen
