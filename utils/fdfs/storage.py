#在windows平台下面fast_FDS没有配置好因此不配置了。
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    '''FDFSStorage文件存储类'''
    def _open(self,name,mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self,name,content):
        '''
        保存文件时使用
        :param name:选择上传的文件名字
        :param content: 包含上传文件内容的File对象
        :return:
        '''
        #创建一个fdfs_client对象
        client = Fdfs_client('./utils/fdfs/client.conf')

        #上传文件到fast_dfs系统中；
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None
        #如果上传失败提示错误信息
        if res.get('Status')  != 'Upload successed.':
            #上传失败
            raise Exception('上传文件到fast dfs失败')
        #获取返回的文件ID
        filename = res.get('Remote file_id')

        return filename

    def exists(self,name):
        '''django判断文件名是否可用'''
        return False
