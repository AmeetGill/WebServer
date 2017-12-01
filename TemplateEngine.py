class TemplateEngine():
    def create_error_page(self,msg,status):
        with open('Error_raw_page.html','r') as f:
            html = f.read()

        with open('Error_raw_page.css','r') as f:
            css = f.read()

        html = html.format(css,status,msg)
        return html
    def display_file(self,path):
        ""
