import importlib.util
from contextlib import contextmanager
import os
import click
import sys
import re

from EulerInit.Convertor.tool.logger import Logger


# trick: 临时修改sys.path以支持动态导入相对路径模块
@contextmanager
def addSysPath(path: str):
    """
    临时向sys.path中增添路径
    :param path: 需增添的路径
    :return: NULL
    """
    import sys
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path = old_path


def pathImport(absolute_path):
    """
    动态导入模块
    :param absolute_path: 模块所在文件夹路径
    :return: module: 模块对象
    """
    with addSysPath(os.path.abspath(os.path.join(__file__, "../.."))):
        spec = importlib.util.spec_from_file_location(absolute_path, absolute_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


# terminal中增加help命令缩写
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


# terminal解析与实际执行
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-m', '--mode', required=True,
              type=click.Choice(['huawei', 'tencent', 'ali', 'template', 'script'], case_sensitive=False),
              help='Target cloud platform to generate.')
@click.option('-p', '--path', required=False, type=click.Path(exists=False, readable=True, writable=True),
              help='Directory for temporary files and output image(default : ./tmp).')
@click.option('-s', '--script', required=False, type=click.Path(exists=False, readable=True, writable=True),
              help='Python script convertor defined by user(if mode is "script").')
@click.option('-t', '--template', required=False, type=click.Path(exists=False, readable=True, writable=True),
              help='Template files directory defined by user(if mode is "template" or "script").')
@click.option('-i', '--img', required=False, type=click.STRING, default='virtual.img',
              help='Output img filename(default : virtual.img).')
@click.option('-f', '--format', required=False, type=click.STRING, default='raw',
              help='Output img format(default : raw).')
@click.option('-q', '--quiet', required=False, is_flag=True,
              help='Quiet mode(not output anything)')
@click.option('--system', required=False,
              type=click.Choice(['x86_64', 'aarch64', 'auto'], case_sensitive=False),
              default='auto',
              help='System architecture of ISO image file(default : auto, "auto" is to fetch from ISO filename).')
@click.option('-v', '--version', required=False,
              type=click.STRING, default='auto',
              help='System version of ISO image file(default : auto, "auto" is to fetch from ISO filename).')
@click.option('--passwd', required=False, default='openEuler@123456',
              help='default password of image root(default : openEuler@123456).')
@click.option('--size', required=False, default='40G',
              help='Image file size to create(default : 40G).')
@click.argument('ISO', type=click.Path(exists=True, readable=True))
def cli(mode: str, path: str, script: str, template: str, img: str, format: str,
        quiet: str, system: str, version: str, passwd: str, size: str, iso: str):
    # 输出重定向
    sys.stdout = Logger('out.log', not quiet)
    sys.stderr = Logger('error.log', not quiet)

    # 确定工作模式
    if mode == 'huawei':
        modulePath = os.path.abspath(os.path.join(__file__, '../Convertor/GeneralConvertor.py'))
        modulUtil = os.path.join(os.path.split(__file__)[0], 'Convertor/template/HUAWEI')
    elif mode == 'tencent':
        modulePath = os.path.abspath(os.path.join(__file__, '../Convertor/GeneralConvertor.py'))
        modulUtil = os.path.join(os.path.split(__file__)[0], 'Convertor/template/TENCENT')
    elif mode == 'ali':
        modulePath = os.path.abspath(os.path.join(__file__, '../Convertor/GeneralConvertor.py'))
        modulUtil = os.path.join(os.path.split(__file__)[0], 'Convertor/template/ALI')
    elif mode == 'template':
        modulePath = os.path.abspath(os.path.join(__file__, '../Convertor/GeneralConvertor.py'))
        modulUtil = template
    elif mode == 'script':
        modulePath = script
        modulUtil = template
    else:
        raise NameError

    # 自动检测平台
    if system == 'auto':
        for system in ['x86_64', 'aarch64']:
            if system in os.path.split(iso)[1]:
                system = system
                break
    if system == 'auto':
        raise NameError('Can not automatic detect the platform'
                        '("x86_64" or "aarch64" must be contained in ISO filename).')

    # 限制只有华为云支持aarch64
    if system == 'aarch64' and mode != 'huawei':
        raise NotImplementedError('AT this time only Huawei cloud platform support aarch64.')

    # 限制script模式任意使用
    if mode == 'script' and os.getenv('EULERINIT_ALLOW_SCRIPT') is not True:
        raise PermissionError('Set environmental variable "EULERINIT_ALLOW_SCRIPT"=True '
                              'to enable user-defined scripts.')

    # 自动检测版本
    if version == 'auto':
        version = re.search('-(\d+\.\d+(-LTS)*)-', iso).group(1)
    if not re.match('\d+\.\d+(-LTS)*', version):
        raise ValueError('Bad version [{version}], version should be something like 20.09 or 20.03-LTS'.
                         format(version=version))

    # 回调接口集合
    callbacks = {
        'echo': click.echo,
        'style': click.style,
        'progressbar': click.progressbar
    }

    # 启动安装流程
    Convertor = pathImport(modulePath)
    conv = Convertor.Convertor()
    conv.setup(iso, modulUtil, system, size, passwd, version, path, callbacks)
    conv.prepare()
    conv.serverUp()
    conv.install()
    conv.serverDown()
    conv.output(img, format)


if __name__ == '__main__':
    cli()
