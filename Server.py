from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import os
import cgi
from SocketServer import ThreadingMixIn
import threading
from PostHandler import PostHandler

class case_cgi_file(object):
    '''Something runnable.'''

    def test(self, handler):
        return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')

    def act(self, handler):
        handler.run_cgi(handler.full_path)

class case_directory_no_index_file(object):
    '''Serve listing for a directory without an index.html page.'''
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and not os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.list_dir(handler.full_path)

class case_no_file():

    def __init__(self):
        '''initialize'''

    def __call__(self):
        '''For calling in for loop'''

        '''File or directory does not exist.'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class case_existing_file():

    def __init__(self):
        '''initialize'''

    def __call__(self):
        '''For calling in for loop'''

    '''File exists.'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_always_fail():

    def __init__(self):
        '''initialize'''

    def __call__(self):
        '''For calling in for loop'''

    '''Base case if nothing else worked.'''
    def test(self, handler):
        return True
    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

class case_directory_index_file(object):

    def __init__(self):
        '''initialize'''

    def __call__(self):
        '''For calling in for loop'''

    '''Serve index.html page for a directory.'''
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))

class RequestHandler(BaseHTTPRequestHandler):
    Page = '''\
    <html>
        <body>
            <table>
                <tr> <td>Header</td>      <td>Value</td> </tr>
                <tr> <td>Date and time</td>    <td>{date_time}</td> </tr>
                <tr> <td>Client host</td>      <td>{client_host}</td> </tr>
                <tr> <td>Client port</td>      <td>{client_port}</td> </tr>
                <tr> <td>Command</td>          <td>{command}</td>  </tr>
                <tr> <td>Path</td>             <td>{path}</td> </tr>
            </table>
        </body>
    </html>
    '''

    Error_Page = '''\
        <html>
            <body>
                <h1>Error accessing {path}</h1>
                <p>{msg}</p>
            </body>
        </html>
    '''

    Listing_Page = '''\
        <html lang="en">
        <head>
          <title>{0}</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
          <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
          <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
        </head>
          <body>
            <div class="container">
              <h2>Index Of {0}</h2>
              <table class="table">
                <thead>
                  <tr>
                    <th>File Name</th>
                  </tr>
                </thead>
                <tbody>
                    {1}
                </tbody>
              </table>
            </div>
          </body>
        </html>
        '''
    Cases = [case_no_file(),case_existing_file(),case_directory_index_file(),case_directory_no_index_file(),case_cgi_file(),case_always_fail()]

    def list_dir(self, full_path):
        colors = ["success","danger","info","warning","active"]
        c_len = len(colors)
        count = 0
        bullets = []
        try:
            entries = os.listdir(full_path)
            for e in entries:
                bootstrap_class = count%c_len
                count += 1
                if e.startswith('.'):
                    break
                bullets.append(' <tr class={1}> <td><a href = {2}>{0} </a></td> </tr>'.format(e,colors[bootstrap_class],self.path+"/"+e))
            page = self.Listing_Page.format("Index Of "+self.path,'\n'.join(bullets))
            self.send_content(page,"html")

        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(self.path, msg)
            self.handle_error(msg)

    def do_GET(self):
        try:

            self.full_path = os.getcwd() + self.path
            print "Request For - "+self.full_path
            for case in self.Cases:
                handler = case
                print handler
                if handler.test(self):
                    handler.act(self)
                    break

        except Exception as msg:
            self.handle_error(msg)
        #page = self.create_page()
        #self.send_page(page)

    def do_POST(self):
        # Parse the form data posted
        print ' POst request'
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Echo back information about what was posted in the form
        form_data = {}
        for field in form.keys():
            field_item = form[field]

            form_data[field] = form[field].value
        print form_data

        p_handler = PostHandler()

        if(p_handler.handle(form_data)==0):
            self.handle_error("Post Function Not Implemented",768)



        self.send_response(200)
        self.end_headers()
        return

    def create_page(self):
        values = {
            'date_time'   : self.date_time_string(),
            'client_host' : self.client_address[0],
            'client_port' : self.client_address[1],
            'command'     : self.command,
            'path'        : self.path
        }
        print self.date_time_string()
        page = self.Page.format(**values)
        return page

    def send_content(self,content,file_type="html",status = 200):
        self.send_response(status)
        self.generate_http_response(content,file_type)
        self.wfile.write(content)

    def handle_file(self,full_path):
        try:
            list_path = full_path.split(".")
            file_type = list_path[len(list_path)-1]
            with open(full_path,'rb') as file:
                content = file.read()
            self.send_content(content,file_type)
        except IOError as msg:
            err = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(err)

    def handle_error(self,msg,status = 404):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content,"html",status)

    def generate_http_response(self,content,file_type="html"):
        print "response file - "+file_type+"\n"
        self.send_header("Content-Type","text"+file_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

    def run_cgi(self, full_path):
        cmd = "python " + full_path
        child_stdin, child_stdout = os.popen2(cmd)
        child_stdin.close()
        data = child_stdout.read()
        child_stdout.close()
        self.send_content(data,"html")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


if __name__ == '__main__':
    serverAddress = ('localhost',8980)
    server = ThreadedHTTPServer(serverAddress, RequestHandler)
    print 'Running at '+str(serverAddress)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
