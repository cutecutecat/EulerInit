from abc import ABCMeta, abstractmethod


class BaseConvertor(metaclass=ABCMeta):
    @abstractmethod
    def setup(self):
        """
        设置相关参数
        :return:NULL
        """
        pass

    @abstractmethod
    def prepare(self):
        """
        准备安装所需文件,一般可能来源：
        1. 下载(可以使用tool/downloader中的相关工具)
        2. 从ISO文件中抽取(可以使用tool/iso中的相关工具)
        3. 在模板文件中指定
        :return: NULL
        """
        pass

    @abstractmethod
    def serverUp(self):
        """
        启动文件服务器，为避免阻塞需要使用新开线程/进程(可以使用tool/fileServer中的相关工具)
        :return: NULL
        """
        pass

    @abstractmethod
    def serverDown(self):
        """
        关闭文件服务器(可以使用tool/fileServer中的相关工具)
        :return: NULL
        """
        pass

    @abstractmethod
    def install(self):
        """
        执行QEMU安装流程(可以使用tool/qemu中的相关工具)：
        1. 分配空间
        2. 实际安装
        :return: NULL
        """
        pass

    @abstractmethod
    def output(self):
        """
        执行镜像生成后续工作，如格式转换或重命名
        :return:
        """
        pass
