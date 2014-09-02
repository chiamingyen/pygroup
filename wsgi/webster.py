#@+leo-ver=5-thin
#@+node:2015.20140902161836.3801: * @file webster.py
#coding: utf-8



#@@language python
#@@tabwidth -4

#@+<<declarations>>
#@+node:2015.20140902161836.3802: ** <<declarations>> (webster)
import os
import sys
import cherrypy
# 導入 pybean 模組與所要使用的 Store 及 SQLiteWriter 方法
from pybean import Store, SQLiteWriter
# 利用 Store  建立資料庫檔案對應物件, 並且設定 frozen=False 表示要開放動態資料表的建立

# 確定程式檔案所在目錄, 在 Windows 有最後的反斜線
_curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
    sys.path.append(os.path.join(os.getenv("OPENSHIFT_REPO_DIR"), "wsgi"))
else:
    sys.path.append(_curdir)

# 設定在雲端與近端的資料儲存目錄
if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
    # 表示程式在雲端執行
    download_root_dir = os.environ['OPENSHIFT_DATA_DIR']
    data_dir = os.environ['OPENSHIFT_DATA_DIR']
else:
    # 表示程式在近端執行
    download_root_dir = _curdir + "/local_data/"
    data_dir = _curdir + "/local_data/"
#@-<<declarations>>
#@+others
#@+node:2015.20140902161836.3803: ** class MyCheck
class MyCheck(object):
    _cp_config = {
        'tools.sessions.on': True
    }

    #@+others
    #@+node:2015.20140902161836.3804: *3* nl2br
    def nl2br(self, string, is_xhtml= True ):
        if is_xhtml:
            return string.replace('\n','<br />\n')
        else :
            return string.replace('\n','<br>\n')
    #@+node:2015.20140902161836.3805: *3* doCheck
    def doCheck(self, word=None):
        if word == None:
            return "<br /><a href=\"/\">首頁</a>|<a href=\"./\">重新查詢</a>"
        #vocabulary = Store(SQLiteWriter(os.environ['OPENSHIFT_REPO_DIR']+"/wsgi/webster_vocabulary.sqlite", frozen=True))
        vocabulary = Store(SQLiteWriter(data_dir+"/webster_vocabulary.sqlite", frozen=True))
        if (vocabulary.count("word","lower(word) like ?", [word]) == 0):
            return "找不到與 "+ word.title() + "有關的資料!"
        else:
            result = vocabulary.find("word","lower(word) like ?", [word])
            output = "以下為 webster 字典查詢:"+word+" 所得到的結果<br /><br />"
            for item in result:
                output += word.title()+"<br /><br />"+str(self.nl2br(item.defn,True))+"<br />"
            output += "<br /><a href=\"/\">首頁</a>|<a href=\"./\">重新查詢</a>"
            return output
    #@+node:2015.20140902161836.3806: *3* index
    doCheck.exposed = True

    def index(self):
        return '''<html>
    <head>
    <title>查字典</title>
    </head>
    <body>
    <form action="doCheck" method="post">
    請輸入要查詢 webster 的單字:<input type="text" name="word" value="" 
        size="15" maxlength="40"/>
    <p><input type="submit" value="查詢"/></p>
    <p><input type="reset" value="清除"/></p>
    </form>
    <br /><a href="/">首頁</a>
    </body>
    </html>'''	
    #@-others
    index.exposed = True
#@-others
if __name__ == '__main__':
    '''
    # 指定程式執行的連接埠號, 內定為 8080
    cherrypy.server.socket_port = 8083
    # 指定程式執行所對應的伺服器 IP 位址, 內定為 127.0.0.1
    cherrypy.server.socket_host = '127.0.0.1'
    '''
    #cherrypy.quickstart(MyCheck())
    # modified for OpenShift
    if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
        application = cherrypy.Application(MyCheck())
    else:
        cherrypy.quickstart(MyCheck())
#@-leo
