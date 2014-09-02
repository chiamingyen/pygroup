#@+leo-ver=5-thin
#@+node:2015.20140902161836.3788: * @file wordnet.py
#coding: utf-8



#@@language python
#@@tabwidth -4

#@+<<declarations>>
#@+node:2015.20140902161836.3789: ** <<declarations>> (wordnet)
import os
import sys
import cherrypy
import sqlite3

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
#@+node:2015.20140902161836.3790: ** class MyCheck
class MyCheck(object):
    _cp_config = {
        'tools.sessions.on': True
    }

    #@+others
    #@+node:2015.20140902161836.3791: *3* nl2br
    def nl2br(self, string, is_xhtml= True ):
        if is_xhtml:
            return string.replace('\n','<br />\n')
        else :
            return string.replace('\n','<br>\n')
    #@+node:2015.20140902161836.3792: *3* printcwd
    def printcwd(self):
        return cwd
    #@+node:2015.20140902161836.3793: *3* doCheck
    printcwd.exposed = True

    def doCheck(self, word=None):
        if word == None:
            return "<br /><a href=\"/\">首頁</a>|<a href=\"./\">重新查詢</a>"
        # 聯結資料庫檔案
        conn = sqlite3.connect(data_dir+"/wordnet30.db")
        # 取得目前 cursor
        cursor = conn.cursor()

        sql = "SELECT word.wordid, synset.synsetid, pos, definition, sample \
        FROM word, sense, synset, sample \
        WHERE word.wordid = sense.wordid \
        AND sense.synsetid = synset.synsetid \
        AND sample.synsetid = synset.synsetid \
        AND lemma = ?"

        output = "以下為 wordnet 字典查詢:"+word+" 所得到的結果<br /><br />"
        count = 0

        for row in cursor.execute(sql, [(word)]):
            count += 1
            output += str(count) + ": " + word.title() + " ("+ str(row[2])+")<br />Defn: " + str(self.nl2br(row[3],True)) + "<br />Sample: "  \
            +  str(self.nl2br(row[4],True)) + "<br /><br />"

        output += "<br /><a href=\"/\">首頁</a>|<a href=\"./\">重新查詢</a>"

        return output
    #@+node:2015.20140902161836.3794: *3* index
    doCheck.exposed = True

    def index(self):
        return '''<html>
<head>
  <title>查字典</title>
</head>
<body>
  <form action="doCheck" method="post">
    請輸入要查詢 wordnet 的單字:<input type="text" name="word" value="" 
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
