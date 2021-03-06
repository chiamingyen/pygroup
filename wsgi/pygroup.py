# -*- coding: utf-8 -*-
'''
Copyright © 2014 Chiaming Yen

Pygroup is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pygroup is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pygroup. If not, see <http://www.gnu.org/licenses/>.

***********************************************************************
'''
########################### 1. 導入所需模組

import cherrypy
import os
### for logincheck
import smtplib
from email.mime.text import MIMEText  
from email.header import Header
### for cmsimply
import cmsimply
### 取得目前時區時間
from time import strftime, localtime
import datetime, pytz
### for pagination
import math
# for mako
from mako.template import Template
from mako.lookup import TemplateLookup
# for bs4
from bs4 import BeautifulSoup, Comment
# 計算執行時間
import time
# for mysql
import pymysql
# for skylark
#from skylark import Database, Model, Field, PrimaryKey, ForeignKey
# use cgi.escape() to resemble php htmlspecialchars()
# use cgi.escape() or html.escape to generate data for textarea tag, otherwise Editor can not deal with some Javascript code.
import cgi
# for logincheck and parse_config methods
import hashlib
# for unescape content
import html.parser
# for logging
import logging
# for strip_tags
import re
# for sqlite
import sqlite3
# 用於 pybean 資料儲存
from pybean import Store, SQLiteWriter
# 再 try peewee
from peewee import SqliteDatabase, Model, CharField, TextField, IntegerField, MySQLDatabase

#logging.basicConfig(level=logging.DEBUG)

#logger = logging.getLogger( __name__ )

########################### 2. 設定近端與遠端目錄
# 確定程式檔案所在目錄, 在 Windows 有最後的反斜線
_curdir = os.path.join(os.getcwd(), os.path.dirname(__file__))
# 設定在雲端與近端的資料儲存目錄
if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
    # 表示程式在雲端執行
    download_root_dir = os.environ['OPENSHIFT_DATA_DIR']
    data_dir = os.environ['OPENSHIFT_DATA_DIR']
    template_root_dir = os.environ['OPENSHIFT_REPO_DIR']+"/wsgi/static"
    # template_root_dir = _curdir + "/static"
else:
    # 表示程式在近端執行
    download_root_dir = _curdir + "/local_data/"
    data_dir = _curdir + "/local_data/"
    template_root_dir = _curdir + "/static"
# 資料庫選用
# 內建使用 sqlite3
ormdb = "sqlite"
#ormdb = "mysql"
#ormdb = "postgresql"
if ormdb == "sqlite":
    # 針對 sqlite3 指定資料庫檔案
    db = SqliteDatabase(data_dir+"task.db", check_same_thread=False)

elif ormdb == "mysql":
    # 選用 MySQL
    # 注意 port 必須為整數, 而非字串
    if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
        db = MySQLDatabase(database='cadp', host=os.environ[str('OPENSHIFT_MYSQL_DB_HOST')],  \
            port=int(os.environ['OPENSHIFT_MYSQL_DB_PORT']), \
            user=os.environ['OPENSHIFT_MYSQL_DB_USERNAME'], \
            passwd=os.environ['OPENSHIFT_MYSQL_DB_PASSWORD'], charset='utf8')
    else:
        # peewee 版本
        db = MySQLDatabase(database='yourdb', host='yourhost', \
             port=3306, user='youruser', passwd='yourpassword', charset='utf8')
else:
    # 選用 PostgreSQL
    # 注意 port 必須為整數, 而非字串
    if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
        db = PostgreSQLDatabase(database='cadp', host=os.environ[str('OPENSHIFT_POSTGRESQL_DB_HOST')],  \
            port=int(os.environ['OPENSHIFT_POSTGRESQL_DB_PORT']), \
            user=os.environ['OPENSHIFT_POSTGRESQL_DB_USERNAME'], \
            passwd=os.environ['OPENSHIFT_POSTGRESQL_DB_PASSWORD'], charset='utf8')
    else:
        # peewee 版本
        db = PostgreSQLDatabase(database='cadp', host='localhost', \
             port=3306, user='root', passwd='root', charset='utf8')
# 在此建立資料表欄位
    
class Task(Model):
    # peewee 內定 id 為 PrimaryKey
    #id = PrimaryKey()
    follow = IntegerField()
    owner = CharField()
    name = CharField()
    type = CharField()
    time = CharField()
    content = TextField()
    ip = CharField()

    class Meta:
        database = db # This model uses the data_dir+"task.db" database.
########################### 3. 建立主物件
class Pygroup(object):
    _cp_config = {
    # if there is no utf-8 encoding, no Chinese input available
    'tools.encode.encoding': 'utf-8',
    'tools.sessions.on' : True,
    'tools.sessions.storage_type' : 'file',
    #'tools.sessions.locking' : 'explicit',
    'tools.sessions.locking' : 'early',
    'tools.sessions.storage_path' : data_dir+'/tmp',
    # session timeout is 60 minutes
    'tools.sessions.timeout' : 60,
    'tools.caching.on' : False
    }
    
    def __init__(self):
        # hope to create downloads and images directories　
        if not os.path.isdir(download_root_dir+"downloads"):
            try:
                os.makedirs(download_root_dir+"downloads")
            except:
                print("mkdir error")
        if not os.path.isdir(download_root_dir+"images"):
            try:
                os.makedirs(download_root_dir+"images")
            except:
                print("mkdir error")
        if not os.path.isdir(download_root_dir+"tmp"):
            try:
                os.makedirs(download_root_dir+"tmp")
            except:
                print("mkdir error")
        if not os.path.isdir(data_dir+"calc_programs"):
            try:
                os.makedirs(data_dir+"calc_programs")
            except:
                print("mkdir error")
        # 若無字典檔案, 則從 local_目錄中複製
        #if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
            #if not os.path.isfile(data_dir+"webster_vocabulary.sqlite"):
                # 尚未完成
        # 假如沒有 adsense_content 則建立一個空白檔案
        if not os.path.isfile(data_dir+"adsense_content"):
            try:
                file = open(data_dir+"adsense_content", "w", encoding="utf-8")
                #  寫入內建的 adsense_content 內容
                adsense_content = '''
    <script type="text/javascript"><!--
    		google_ad_client = "pub-2140091590744860";
    		google_ad_width = 300;
    		google_ad_height = 250;
    		google_ad_format = "300x250_as";
    		google_ad_type = "image";
    		google_ad_channel ="";
    		google_color_border = "000000";
    		google_color_link = "0000FF";
    		google_color_bg = "FFFFFF";
    		google_color_text = "000000";
    		google_color_url = "008000";
    		google_ui_features = "rc:0";
    		//--></script>
    		<script type="text/javascript"
    		src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
    		</script>

    <script type="text/javascript"><!--
    		google_ad_client = "pub-2140091590744860";
    		google_ad_width = 300;
    		google_ad_height = 250;
    		google_ad_format = "300x250_as";
    		google_ad_type = "image";
    		google_ad_channel ="";
    		google_color_border = "000000";
    		google_color_link = "0000FF";
    		google_color_bg = "FFFFFF";
    		google_color_text = "000000";
    		google_color_url = "008000";
    		google_ui_features = "rc:0";
    		//--></script>
    		<script type="text/javascript"
    		src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
    		</script><br />
    '''
                file.write(adsense_content+"\n")
                file.close()
            except:
                print("mkdir error")
        if ormdb == "sqlite":
            # 資料庫使用 SQLite
            # 這裡應該要使用 peewee 建立資料庫與表格
            try:
                conn = sqlite3.connect(data_dir+"task.db")
                cur = conn.cursor()
                # 建立資料表
                cur.execute("CREATE TABLE IF NOT EXISTS task( \
                        id INTEGER PRIMARY KEY AUTOINCREMENT, \
                        name TEXT, \
                        owner TEXT, \
                        type TEXT, \
                        time TEXT, \
                        content TEXT, \
                        ip TEXT, \
                        follow INTEGER);")
                cur.close()
                conn.close()
            except:
                print("can not create db and table")
        elif ormdb == "mysql":
            # 嘗試建立資料庫與資料表
            # 這裡應該要使用 peewee 建立資料庫與表格
            if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
                host=str(os.environ[str('OPENSHIFT_MYSQL_DB_HOST')])
                port=int(os.environ[str('OPENSHIFT_MYSQL_DB_PORT')])
                db='cadp'
                user=str(os.environ[str('OPENSHIFT_MYSQL_DB_USERNAME')])
                passwd=str(os.environ[str('OPENSHIFT_MYSQL_DB_PASSWORD')])
            else:
                host="yourhost"
                port=3306
                db='yourdb'
                user='youruser'
                passwd='yourpassword'
            charset='utf8'
            # 案例建立時, 就嘗試建立資料庫與資料表
            try:
                conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, charset=charset)
                # 建立資料庫
                cur = conn.cursor()
                cur.execute("CREATE DATABASE IF NOT EXISTS "+db+" CHARACTER SET UTF8;")
                # 建立資料表
                cur.execute("USE "+db+";")
                cur.execute("CREATE TABLE IF NOT EXISTS `task` ( \
                    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT, \
                    `name` VARCHAR(255) NOT NULL COLLATE 'utf8_unicode_ci', \
                    `owner` VARCHAR(255) NOT NULL COLLATE 'utf8_unicode_ci', \
                    `type` VARCHAR(255) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci', \
                    `time` DATETIME NOT NULL COLLATE 'utf8_unicode_ci', \
                    `content` LONGTEXT COLLATE 'utf8_unicode_ci', \
                    `ip` VARCHAR(255) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci', \
                    `follow` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0', \
                    PRIMARY KEY (`id`)) \
                    COLLATE='utf8_general_ci' default charset=utf8 ENGINE=InnoDB;")
                cur.close()
                conn.close()
            except:
                print("can not create db and table")
        else:
            # 使用 PostgreSQL
            # 嘗試建立資料庫與資料表
            # 這裡應該要使用 peewee 建立資料庫與表格
            if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
                host=str(os.environ[str('OPENSHIFT_POSTGRESQL_DB_HOST')])
                port=int(os.environ[str('OPENSHIFT_POSTGRESQL_DB_PORT')])
                db='cadp'
                user=str(os.environ[str('OPENSHIFT_POSTGRESQL_DB_USERNAME')])
                passwd=str(os.environ[str('OPENSHIFT_POSTGRESQL_DB_PASSWORD')])
            else:
                host="localhost"
                port=3306
                db='cadp'
                user='root'
                passwd='root'
            charset='utf8'
            # 案例建立時, 就嘗試建立資料庫與資料表
            try:
                conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, charset=charset)
                # 建立資料庫
                cur = conn.cursor()
                cur.execute("CREATE DATABASE IF NOT EXISTS "+db+";")
                # 建立資料表
                cur.execute("USE "+db+";")
                cur.execute("CREATE TABLE IF NOT EXISTS `task` ( \
                    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT, \
                    `name` VARCHAR(255) NOT NULL COLLATE 'utf8_unicode_ci', \
                    `owner` VARCHAR(255) NOT NULL COLLATE 'utf8_unicode_ci', \
                    `type` VARCHAR(255) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci', \
                    `time` DATETIME NOT NULL COLLATE 'utf8_unicode_ci', \
                    `content` LONGTEXT COLLATE 'utf8_unicode_ci', \
                    `ip` VARCHAR(255) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci', \
                    `follow` BIGINT(20) UNSIGNED NOT NULL DEFAULT '0', \
                    PRIMARY KEY (`id`)) \
                    COLLATE='utf8_general_ci' default charset=utf8 ENGINE=InnoDB;")
                cur.close()
                conn.close()
            except:
                print("can not create db and table")
    @cherrypy.expose
    def usermenu(self):
        # 這裡包括列出用戶以及列印表單
        user = self.printuser()
        menu = ["login", "logout", "usermenu", "cmsimply", \
                     "tasklist"]
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        # 必須要從 templates 目錄取出 usermenu.html
        mytemplate = template_lookup.get_template("usermenu.html")
        return mytemplate.render(user=user, menu=menu)
    def printuser(self):
        # 取得 user 資料
        try:
            user = cherrypy.session["user"]
        except:
            user = "anonymous"
        if user == "":
            user = "anonymous"
        return user
    # 不允許使用者直接呼叫 taskform
    def taskform(self, id=0, *args, **kwargs):
        user = self.printuser()
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        # 必須要從 templates 目錄取出 tasklist.html
        # 針對 id != 0 時, 表示要回應主資料緒, 希望取出與 id 對應的資料標頭, 然後加上 Re:
        mytemplate = template_lookup.get_template("taskform.html")
        return mytemplate.render(user=user, id=id)
    @cherrypy.expose
    def taskaction(self, type=None, name=None, follow=0, content=None, ip=None, *args, **kwargs):
        if content == None or name == "":
            return "標題與內容都不可空白!<br /><a href='/'>Go to main page</a><br />"
        else:
            start_time = time.time()
            owner = self.printuser()
            if self.allow_pass(owner) == "no":
                raise cherrypy.HTTPRedirect("login")
            ip = self.client_ip()
            now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
            '''
            # 因為登入後就將 @ 代換為 _at_, 所以此地不用再換
            # user 若帶有 @ 則用 at 代替
            if "@" in owner:
                owner = owner.replace('@', '_at_')
            '''
            content = content.replace('\n', '')
            valid_tags = ['a', 'br', 'h1', 'h2', 'h3', 'p', 'div', 'hr', 'img', 'iframe', 'li', 'ul', 'b', 'ol', 'pre']
            tags = ''
            for tag in valid_tags:
                tags += tag
            content = self.strip_tags(content, tags)
            # 這裡要除掉 </br> 關閉 break 的標註, 否則在部分瀏覽器會產生額外的跳行
            content = str(content).replace('</br>', '')
            time_elapsed = round(time.time() - start_time, 5)
            # last insert id 為 data.id
            db.connect()
            # peewee 版本
            data = Task.create(owner=owner, name=str(name), type=type, time=str(now), follow=follow, content=content, ip=str(ip))
            data.save()
            # 這裡要與 taskedit 相同, 提供回到首頁或繼續編輯按鈕
            output = "<a href='/'>Go to main page</a><br />"
            output +="<a href='/taskeditform?id="+str(data.id)+"'>繼續編輯</a><br /><br />"
            output += '''以下資料已經更新:<br /><br />
            owner:'''+owner+'''<br />
            name:'''+name+'''<br />
            type:'''+type+'''<br />
            time:'''+str(now)+'''<br />
            content:'''+str(content)+'''<br /><br />
            <a href='/'>Go to main page</a><br />
        '''
            output +="<a href='/taskeditform?id="+str(data.id)+"'>繼續編輯</a><br /><br />"
            db.close()
            return output
        # 原先直接轉到 tasklist 方法 (index)
        #raise cherrypy.HTTPRedirect("tasklist")
    @cherrypy.expose
    # 從 tasklist 改為 index
    def index(self, page=1, item_per_page=5, id=0, flat=0, desc=0, keyword=None, *args, **kwargs):
        user = self.printuser()
        # 這裡不用 self.allow_pass 原因在於需要 adsense 變數
        saved_password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if user == "anonymous" and anonymous != "yes":
            if id != 0:
                raise cherrypy.HTTPRedirect("login?id="+id)
            else:
                raise cherrypy.HTTPRedirect("login")
        if adsense == "yes":
            filename = data_dir+"adsense_content"
            with open(filename, encoding="utf-8") as file:
                adsense_content = file.read()
        else:
            adsense_content = ""
        #ip = cherrypy.request.remote.ip
        ip = self.client_ip()
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        # 必須要從 templates 目錄取出 tasklist2.html
        mytemplate = template_lookup.get_template("tasklist.html")
        # 這裡要加入單獨根據 id 號, 列出某一特定資料緒的分支
        # 若 id 為 0 表示非指定列出各別主緒資料, 而是列出全部資料
        # 這時可再根據各筆資料列印時找出各主緒資料的附屬資料筆數
        # 加入 flat = 1 時, 列出所有資料
        # 請注意這裡直接從 tasksearchform.html 中的關鍵字查詢, 指定以 tasklist 執行, 但是無法單獨列出具有關鍵字的 task 資料, 而是子緒有關鍵字時, 也是列出主緒資料
        # 單獨 db 連結與結束
        db.connect()
        if keyword == None:
            if id == 0:
                if flat == 0:
                    # 只列出主資料緒
                    # desc 為 0 表示要 id 由小到大排序列出資料
                    if desc == 0:
                        method = "?"
                        data = Task.select().where(Task.follow==0)
                    else:
                        # desc 為 1 表示 id 反向排序
                        method = "?desc=1"
                        data = Task.select().where(Task.follow==0).order_by(Task.id.desc())
                else:
                    # flat 為 1 表示要列出所有資料
                    # 原先沒有反向排序, 內建使用正向排序
                    if desc == 0:
                        method = "?flat=1"
                        data = Task.select()
                    else:
                        method = "?flat=1&desc=1"
                        data = Task.select().order_by(Task.id.desc())
            else:
                method = "?id="+str(id)
                # 設法列出主資料與其下屬資料緒, 這裡是否可以改為 recursive 追蹤多緒資料
                # 只列出主緒與下一層子緒資料
                data = Task.select().where((Task.id == id) | (Task.follow == id))
        else:
            # 有關鍵字查詢時(只查 owner, content, type 與 name), 只列出主資料緒
            #flat = 1
            method = "?keyword="+keyword+"&flat="+str(flat)
            data = Task.select().where((Task.content ** ('%%%s%%' % (keyword))) | (Task.name ** ('%%%s%%' % (keyword))) | \
            (Task.owner ** ('%%%s%%' % (keyword))) | \
            (Task.type ** ('%%%s%%' % (keyword))) \
                )
        follow = []
        for task in data:
            follow_data = Task.select().where(Task.follow == task.id).count()
            follow.append(follow_data)
        db.close()
        #
        # 送出 user, id, flat, method 與 data
        #
        # 增加傳送 read_only, 若 read_only = yes 則不列出 taskform, 而且所有新增編輯刪除功能均失效
        #
        return mytemplate.render(user=user, id=id, flat=flat, method=method, data=data,  \
            page=page, item_per_page=item_per_page, ip=ip, follow=follow, keyword=keyword, \
            adsense_content=adsense_content, adsense=adsense, anonymous=anonymous, \
            site_closed=site_closed, read_only=read_only)
        # 其餘分頁 logic 在 mako template tasklist.html 中完成
    def allow_pass(self, user="anonymous"):
        password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if user == "anonymous" and anonymous != "yes":
            return "no"
        else:
            return "yes"
    ## Remove xml style tags from an input string.
    #
    #  @param string The input string.
    #  @param allowed_tags A string to specify tags which should not be removed.
    def strip_tags(self, string, allowed_tags=''):
      if allowed_tags != '':
        # Get a list of all allowed tag names.
        allowed_tags_list = re.sub(r'[\\/<> ]+', '', allowed_tags).split(',')
        allowed_pattern = ''
        for s in allowed_tags_list:
          if s == '':
           continue;
          # Add all possible patterns for this tag to the regex.
          if allowed_pattern != '':
            allowed_pattern += '|'
          allowed_pattern += '<' + s + ' [^><]*>$|<' + s + '>|<!--' + s + '-->'
        # Get all tags included in the string.
        all_tags = re.findall(r'<!--?[^--><]+>', string, re.I)
        for tag in all_tags:
          # If not allowed, replace it.
          if not re.match(allowed_pattern, tag, re.I):
            string = string.replace(tag, '')
      else:
        # If no allowed tags, remove all.
        string = re.sub(r'<[^>]*?>', '', string)
     
      return string
    def client_ip(self):
        try:
            return cherrypy.request.headers["X-Forwarded-For"]
        except:
            return cherrypy.request.headers["Remote-Addr"]
    # default method, if there is no corresponding method, cherrypy will redirect to default method
    # need *args and **kwargs as input variables for all possible URL links
    @cherrypy.expose
    # default can not live with calc method?
    def default(self, attr='default', *args, **kwargs):
        raise cherrypy.HTTPRedirect("/")
    @cherrypy.expose
    def save_program(self, filename=None, sheet_content=None):
        with open(data_dir+"/calc_programs/"+filename, "wt", encoding="utf-8") as out_file:
            data = sheet_content.replace("\r\n", "\n")
            out_file.write(data)

        return str(filename)+" saved!<br />"
    @cherrypy.expose
    @cherrypy.expose
    # 登入表單, 使用 gmail 帳號與密碼登入
    def login(self, id=0, *args, **kwargs):
        # 當使用者要求登入時, 將 user session 清除
        #cherrypy.session["user"] = ""
        saved_password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        mytemplate = template_lookup.get_template("login.html")
        return mytemplate.render(site_closed=site_closed, read_only=read_only, id=id)
    @cherrypy.expose
    def logincheck(self, id=0, account=None, password=None):
        saved_password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if account != None and password != None:
            # 這裡要加入用戶名稱為 admin 的管理者登入模式
            if account == "admin":
                # 進入 admin 密碼查驗流程
                hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
                if hashed_password == saved_password:
                    cherrypy.session['user'] = "admin"
                    raise cherrypy.HTTPRedirect("/?id="+str(id))
                else:
                    return "login failed.<br /><a href='/'>Go to main page</a><br />"
            else:
                # 一般帳號查驗
                if site_closed == "yes":
                    return "抱歉!網站關閉中"
                elif not mail_suffix in account or mail_suffix != "":
                    return "抱歉!此類帳號不允許登入"
                else:
                    server = smtplib.SMTP('smtp.gmail.com:587')
                    server.ehlo()
                    server.starttls()
                    try:
                        server.login(account, password)
                        server.quit()
                        if "@" in account:
                            account = account.replace('@', '_at_')
                        cherrypy.session["user"] = account
                        #return account+" login successfully."
                        #若登入成功, 則離開前跳到根目錄
                    except:
                        server.quit()
                        return "login failed.<br /><a href='/'>Go to main page</a><br />"
        else:
            raise cherrypy.HTTPRedirect("login?id="+str(id))
        raise cherrypy.HTTPRedirect("/?id="+str(id))
    @cherrypy.expose
    def editconfig(self, password=None, password2=None, adsense=None, anonymous=None, \
                    mail_suffix=None, site_closed=None, read_only=None):
        filename = "pygroup_config"
        user = self.printuser()
        # 只有系統管理者可以編輯 config 設定檔案
        if user != "admin":
            raise cherrypy.HTTPRedirect("login")
        if password == None or adsense == None or anonymous == None:
            return self.error_log("no content to save!")
        # 取出目前的設定值
        old_password, old_adsense, old_anonymous, old_mail_suffix, old_site_closed, old_read_only = self.parse_config(filename=filename)
        if adsense == None or password == None or password2 != old_password or password == '':
            # 傳回錯誤畫面
            return "error<br /><a href='/'>Go to main page</a><br />"
        else:
            if password == password2 and password == old_password:
                hashed_password = old_password
            else:
                hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
            # 將新的設定值寫入檔案
            file = open(data_dir+filename, "w", encoding="utf-8")
            #  將新的設定值逐一寫入設定檔案中
            file.write("password:"+hashed_password+"\n \
                adsense:"+adsense+"\n \
                anonymous:"+anonymous+"\n \
                mail_suffix:"+mail_suffix+"\n \
                site_closed:"+site_closed+"\n \
                read_only:"+read_only+"\n")
            file.close()
            # 傳回設定檔案已經儲存
            return "config file saved<br /><a href='/'>Go to main page</a><br />"
    @cherrypy.expose
    def editconfigform(self, *args, **kwargs):
        user = self.printuser()
        # 只有系統管理者可以編輯 config 設定檔案
        if user != "admin":
            raise cherrypy.HTTPRedirect("login")
        # 以下設法列出 config 編輯表單
        # 取出目前的設定值
        saved_password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        mytemplate = template_lookup.get_template("editconfigform.html")
        return mytemplate.render(user=user, saved_password=saved_password, adsense=adsense, anonymous=anonymous, mail_suffix=mail_suffix, site_closed=site_closed, read_only=read_only)
    @cherrypy.expose
    def editadsense(self, adsense_content=None):
        filename = "adsense_content"
        user = self.printuser()
        # 只有系統管理者可以編輯 config 設定檔案
        if user != "admin":
            raise cherrypy.HTTPRedirect("login")
        # 將新的設定值寫入檔案
        file = open(data_dir+filename, "w", encoding="utf-8")
        #  將新的設定值逐一寫入設定檔案中
        file.write(adsense_content+"\n")
        file.close()
        # 傳回設定檔案已經儲存
        return "adsense_content file saved"
    @cherrypy.expose
    def editadsenseform(self, *args, **kwargs):
        user = self.printuser()
        # 只有系統管理者可以編輯 adsense_content 檔案
        if user != "admin":
            raise cherrypy.HTTPRedirect("login")
        # 以下設法列出 adsense_content 編輯表單
        # 取出目前的設定值
        filename="adsense_content"
        # 取出 adsense_content 後, 傳回
        with open(data_dir+filename, encoding="utf-8") as file:
            saved_adsense = file.read()
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        mytemplate = template_lookup.get_template("editadsenseform.html")
        return mytemplate.render(user=user, saved_adsense=saved_adsense)
    def parse_config(self, filename):
        #filename = "pygroup_config"
        if not os.path.isfile(data_dir+filename):
            # create config file if there is no config file
            file = open(data_dir+filename, "w", encoding="utf-8")
            # 若無設定檔案, 則逐一寫入 default 值
            # default password is admin
            password="admin"
            hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()
            # adsense 為 yes 表示要放廣告, 內建 adsense 為 no
            # anonymouse 為 yes 表示允許無登入者可以檢視內容, 內建 anonymous 為 no
            file.write("password:"+hashed_password+"\n \
                adsense:no\n \
                anonymous:no\n \
                user_mail_suffix:\n \
                site_closed:no\n \
                read_only:no\n")
            file.close()
        # 取出設定值後, 傳回
        with open(data_dir+filename, encoding="utf-8") as file:
            config = file.read()
        config_data = config.split("\n")
        password = config_data[0].split(":")[1]
        adsense = config_data[1].split(":")[1]
        anonymous = config_data[2].split(":")[1]
        mail_suffix = config_data[3].split(":")[1]
        site_closed = config_data[4].split(":")[1]
        read_only = config_data[5].split(":")[1]
        return password, adsense, anonymous, mail_suffix, site_closed, read_only
    @cherrypy.expose
    def logout(self, *args, **kwargs):
        cherrypy.session.delete()
        return "已經登出!<br /><a href='/'>Go to main page</a><br />"
        #raise cherrypy.HTTPRedirect("")
    @cherrypy.expose
    def taskeditform(self, id=None, *args, **kwargs):
        user = self.printuser()
        password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if read_only == "yes" and user != "admin":
            return "<a href='/'>Go to main page</a><br /><br />error, site is read only!"
        if user == "anonymous" and anonymous != "yes":
            raise cherrypy.HTTPRedirect("login")
        else:
            try:
                db.connect()
                # 用 get() 取單筆資料
                data = Task.select().where(Task.id==int(id)).get()
                output = "user:"+user+", owner:"+data.owner+"<br /><br />"
                if user != data.owner:
                    if user != "admin":
                        db.close()
                        return output + "error! Not authorized!"
                    else:
                        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
                        mytemplate = template_lookup.get_template("taskeditform.html")
                        db.close()
                        return mytemplate.render(user=user, id=id, data=data)
                else:
                    template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
                    mytemplate = template_lookup.get_template("taskeditform.html")
                    db.close()
                    return mytemplate.render(user=user, id=id, data=data)
            except:
                db.close()
                return "error! Not authorized!"
    @cherrypy.expose
    def taskedit(self, id=None, type=None, name=None, content=None, *args, **kwargs):
        # check user and data owner
        if id == None:
            return "error<br /><br /><a href='/'>Go to main page</a><br />"
        user = self.printuser()
        password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if read_only == "yes" and user != "admin":
            return "<a href='/'>Go to main page</a><br /><br />error, site is read only!"
        if user == "anonymous" and anonymous != "yes":
            raise cherrypy.HTTPRedirect("login")
        try:
            db.connect()
        except:
            time.sleep(0.300)
            db.connect()
        data = Task.select().where(Task.id==int(id)).get()
        now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
        # 過濾資料
        content = content.replace('\n', '')
        valid_tags = ['a', 'br', 'h1', 'h2', 'h3', 'p', 'div', 'hr', 'img', 'iframe', 'li', 'ul', 'b', 'ol', 'pre']
        tags = ''
        for tag in valid_tags:
            tags += tag
        content = self.strip_tags(content, tags)
        # 這裡要除掉 </br> 關閉 break 的標註, 否則在部分瀏覽器會產生額外的跳行
        content = str(content).replace('</br>', '')
        output = "user:"+user+", owner:"+data.owner+"<br /><br />"
        if user != data.owner:
            if  user != "admin":
                db.close()
                return "error! Not authorized!"
            else:
                # 請注意這裡曾經犯了 where(id==int(id) 的重大錯誤, 讓所有資料在 update 時只留下一筆資料
                query = Task.update(type=type, name=name, content=str(content), time=str(now)).where(Task.id==int(id))
                query.execute()
                output += "<a href='/'>Go to main page</a><br />"
                output +="<a href='/taskeditform?id="+str(id)+"'>繼續編輯</a><br /><br />"
                output += '''以下資料已經更新:<br /><br />
                owner:'''+data.owner+'''<br />
                name:'''+name+'''<br />
                type:'''+type+'''<br />
                time:'''+str(now)+'''<br />
                content:'''+str(content)+'''<br /><br />
                <a href='/'>Go to main page</a><br />
    '''
                output +="<a href='/taskeditform?id="+str(id)+"'>繼續編輯</a><br />"
        else:
            query = Task.update(type=type, name=name, content=str(content), time=str(now)).where(Task.id==int(id))
            query.execute()
            output += "<a href='/'>Go to main page</a><br />"
            output +="<a href='/taskeditform?id="+str(id)+"'>繼續編輯</a><br /><br />"
            output += '''以下資料已經更新:<br /><br />
            owner:'''+data.owner+'''<br />
            name:'''+name+'''<br />
            type:'''+type+'''<br />
            time:'''+str(now)+'''<br />
            content:'''+str(content)+'''<br /><br />
            <a href='/'>Go to main page</a><br />
    '''
            output +="<a href='/taskeditform?id="+str(id)+"'>繼續編輯</a><br />"
        db.close()
        return output
    @cherrypy.expose
    def taskdeleteform(self, id=None, *args, **kwargs):
        user = self.printuser()
        password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if read_only == "yes" and user != "admin":
            return "<a href='/'>Go to main page</a><br /><br />error, site is read only!"
        if user == "anonymous" and anonymous != "yes":
            raise cherrypy.HTTPRedirect("login")
        else:
            try:
                # 這裡要區分刪除子緒或主緒資料
                # 若刪除子緒, 則 data 只包含子緒資料, 若為主緒, 則 data 必須包含所有資料
                # 先找出資料, 判定是否為主緒
                # 用 get() 取單筆資料
                db.connect()
                data= Task.select().where(Task.id==int(id)).get()
                owner = data.owner
                if user != data.owner:
                    if user != "admin":
                        db.close()
                        return output + "error! 非資料擁有者, Not authorized!"
                    else:
                        if data.follow == 0:
                            # 表示該資料為主緒資料
                            # 資料要重新搜尋, 納入子資料
                            data = Task.select().where((Task.id == id) | (Task.follow == id))
                            output = "資料為主緒資料<br />"
                            # 增加一個資料類型判斷, main 表資料為主緒
                            type = "main"
                        else:
                            # 表示該資料為子緒資料
                            # 直接採用 data 資料送到 taskdeleteform.html
                            output = "資料為子緒資料<br />"
                            # 增加一個資料類型判斷, alone 表資料為子緒
                            type = "alone"
                        output += "user:"+user+", owner:"+owner+"<br /><br />"
                        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
                        mytemplate = template_lookup.get_template("taskdeleteform.html")
                        # 這裡的 type 為所要刪除資料的類型, 為 main 或為 alone
                        db.close()
                        return mytemplate.render(user=user, id=id, data=data, type=type)
                else:
                    if data.follow == 0:
                        # 表示該資料為主緒資料
                        # 資料要重新搜尋, 納入子資料
                        data = Task.select().where((Task.id == id) | (Task.follow == id))
                        output = "資料為主緒資料<br />"
                        # 增加一個資料類型判斷, main 表資料為主緒
                        type = "main"
                    else:
                        # 表示該資料為子緒資料
                        # 直接採用 data 資料送到 taskdeleteform.html
                        output = "資料為子緒資料<br />"
                        # 增加一個資料類型判斷, alone 表資料為子緒
                        type = "alone"
                    output += "user:"+user+", owner:"+owner+"<br /><br />"
                    template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
                    mytemplate = template_lookup.get_template("taskdeleteform.html")
                    # 這裡的 type 為所要刪除資料的類型, 為 main 或為 alone
                    db.close()
                    return mytemplate.render(user=user, id=id, data=data, type=type)
            except:
                db.close()
                return "error! 無法正確查詢資料, Not authorized!"
    @cherrypy.expose
    def taskdelete(self, id=None, type=None, name=None, content=None, *args, **kwargs):
        # check user and data owner
        user = self.printuser()
        password, adsense, anonymous, mail_suffix, site_closed, read_only = self.parse_config(filename="pygroup_config")
        if read_only == "yes" and user != "admin":
            return "<a href='/'>Go to main page</a><br /><br />error, site is read only!"
        if user == "anonymous" and anonymous != "yes":
            raise cherrypy.HTTPRedirect("login")
        # 用 get() 取單筆資料
        db.connect()
        data = Task.select().where(Task.id==int(id)).get()
        now = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
        output = "user:"+user+", owner:"+data.owner+"<br /><br />"
        if user != data.owner:
            if user != "admin":
                db.close()
                return "error! Not authorized!"
            else:
                # 若資料為主緒則一併刪除子緒, 若為子緒, 則只刪除該子緒
                if data.follow == 0:
                    # 表示資料為主緒
                    # 先刪除主緒
                    query = Task.at(int(id)).delete()
                    query.execute()
                    # 再刪除所有對應子緒
                    query = Task.delete().where(follow=int(id))
                    query.execute()
                    output += "所有序列資料已經刪除!<br />"
                else:
                    # 表示資料為子緒
                    query = Task.delete().where(Task.id==int(id))
                    query.execute()
                    output += "資料已經刪除!<br />"
        else:
            # 若資料為主緒則一併刪除子緒, 若為子緒, 則只刪除該子緒
            if data.follow == 0:
                # 表示資料為主緒
                # 先刪除主緒
                query = Task.delete().where(Task.id==int(id))
                query.execute()
                # 再刪除所有對應子緒
                query = Task.delete().where(Task.follow==int(id))
                query.execute()
                output += '''所有序列資料已經刪除!<br /><br />
                <a href='/'>Go to main page</a><br />
    '''
            else:
                # 表示資料為子緒
                query = Task.delete().where(Task.id==int(id))
                query.execute()
                output += '''資料已經刪除!<br /><br />
                <a href='/'>Go to main page</a><br />
    '''
        db.close()
        return output
    # 不允許使用者直接呼叫 tasksearchform
    def tasksearchform(self, *args, **kwargs):
        user = self.printuser()
        template_lookup = TemplateLookup(directories=[template_root_dir+"/templates"])
        # 必須要從 templates 目錄取出 tasksearchform.html
        mytemplate = template_lookup.get_template("tasksearchform.html")
        return mytemplate.render(user=user)
########################### 4. 安排啟動設定
# 配合程式檔案所在目錄設定靜態目錄或靜態檔案
application_conf = {
        '/static':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': _curdir+"/static"},
        'images':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': data_dir+"/images"},
        'downloads':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': data_dir+"/downloads"},
        'brython_programs':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': data_dir+"/brython_programs"},
        'calc_programs':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': data_dir+"/calc_programs"},
        '/':{
        'tools.staticdir.on': True,
        'tools.staticdir.dir': _curdir+"/static/openjscad"},
        # 設定靜態 templates 檔案目錄對應
        '/templates':{
        'tools.staticdir.on': True,
        'tools.staticdir.root': template_root_dir,
        'tools.staticdir.dir': 'templates',
        'tools.staticdir.index' : 'index.htm'
        }
    }

########################### 5. 在近端或遠端啟動程式
# 利用 Pygroup() class 產生案例物件
root = Pygroup()
# 導入 CMSimply 內容管理模組
#root.cmsimply = cmsimply.CMSimply()
# 使用命名節點中所定義的 cmsimply_group 類別
#root.cmsimply = cmsimply_group()
root.cmsimply = cmsimply.CMSimply()
# 導入 Download
root.cmsimply.download = cmsimply.Download()

if __name__ == '__main__':
    # 假如在 os 環境變數中存在 'OPENSHIFT_REPO_DIR', 表示程式在 OpenShift 環境中執行
    if 'OPENSHIFT_REPO_DIR' in os.environ.keys():
        # 雲端執行啟動
        application = cherrypy.Application(root, config = application_conf)
    else:
        # 近端執行啟動
        '''
        cherrypy.server.socket_port = 8083
        cherrypy.server.socket_host = '127.0.0.1'
        '''
        cherrypy.quickstart(root, config = application_conf)
