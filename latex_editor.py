from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label 
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.filechooser import FileChooserListView
from pdf2image import convert_from_path
import re
import os
import subprocess
import shutil

keywords_dic = {
    '[': r'\[ \]',
    'frac': r'\frac{x}{y}',
    'begin': '\\begin{}\n\n\n\n\\end{}'
}

key_reg = r'=(\S*)\ '

LabelBase.register(name='courier', fn_regular='fonts/cour.ttf')

class LaTeXEditorApp(App):
    def build(self):
        self.title='LaTeX Editor'

        self.main_layout = GridLayout(cols=4, padding=20, spacing=20)

        self.side_menu = GridLayout(rows=3, size_hint_x = .15, spacing=5)
        self.save_button = Button(text='Save', on_release=self.save)
        self.side_menu.add_widget(self.save_button)
        self.load_button = Button(text='Load', on_release=self.load_view)
        self.side_menu.add_widget(self.load_button)

        self.main_layout.add_widget(self.side_menu)

        self.text_box = self.text_input = TextInput(text='\\documentclass[12pt]{article}\n\\begin{document}\n\nYour Work Here\n\n\\end{document}', font_name='courier')
        self.text_box.bind(text = self.keywords)
        self.main_layout.add_widget(self.text_box)

        self.center_menu = GridLayout(rows=5, cols=1, spacing=5, size_hint_x = .15)
        self.main_layout.add_widget(self.center_menu)
        self.zoomin_button = Button(text='+', on_release = self.zoomin, size_hint_y = .1)
        self.center_menu.add_widget(self.zoomin_button)
        self.zoomout_button = Button(text='-', on_release = self.zoomout, size_hint_y = .1)
        self.center_menu.add_widget(self.zoomout_button)

        self.pageselect_layout = GridLayout(cols=2,  spacing=5, size_hint_y=.1)
        self.prevpage_button = Button(text='<--', on_release=lambda run: self.change_page(False))
        self.pageselect_layout.add_widget(self.prevpage_button)
        self.nextpage_button = Button(text='-->', on_release=lambda run: self.change_page(True))
        self.pageselect_layout.add_widget(self.nextpage_button)
        self.center_menu.add_widget(self.pageselect_layout)

        self.run_button = Button(text='Run', on_release = self.update_output)
        self.center_menu.add_widget(self.run_button)
        self.saveimg_button = Button(text=' Save \nImage', on_release = self.save_image, size_hint_y = .2)
        self.center_menu.add_widget(self.saveimg_button)

        self.output_scroll = ScrollView()
        self.output_image = Image(source = 'latex_output/disp_jpg/latex_raw-0.jpg', size_hint=(None, None), size=(1200, 1200), allow_stretch = True)
        self.output_scroll.add_widget(self.output_image)
        self.main_layout.add_widget(self.output_scroll)

        self.file_path = ''

        self.update_output(None)

        Window.size = (1440, 800)
        Window.top = 0
        Window.left = 0
        return self.main_layout

    def keywords(self, OBJECT, text):
        for m in re.finditer(key_reg, text):
            for keyword in keywords_dic:
                if m.group(1) == keyword:
                    start, end = m.span()
                    text1 = text[:start]
                    text2 = text[end:]
                    self.text_box.text = text1+keywords_dic[keyword]+text2
        return self.text_box.text 

    def zoomin(self, OBJECT):
        image_size = self.output_image.size[0] * 1.1
        self.output_image.size = [image_size, image_size]
    def zoomout(self, OBJECT):
        image_size = self.output_image.size[0] / 1.1
        self.output_image.size = [image_size, image_size]

    def update_output(self, OBJECT):
        with open('latex_output/latex_raw.TeX', 'w') as fout:
            fout.write(self.text_box.text)
        r = subprocess.run(['/Library/TeX/texbin/pdflatex', '-output-format=pdf', '-interaction=nonstopmode', 'latex_raw.TeX'], cwd='latex_output', capture_output = True)

        images = convert_from_path('latex_output/latex_raw.pdf')
        for num, image in enumerate(images):
            image.save(f'latex_output/disp_jpg/latex_raw-{num}.jpg', 'JPEG')

        error = str(r.stdout).split('\\n')
        '''
        if len(error) > 14:
            self.latex_error(error)
        '''
        self.output_image.reload()

    def latex_error(self, error):
        print(error)
        for i in range(11):
            error.pop(0)
        error = f'{error[0]} {error[1]} .'
        layout = GridLayout(cols = 1, padding = 10, spacing=20)
        popupText = TextInput(text = error, readonly = True)
        closeButton = Button(text = "Acknowledge")
        layout.add_widget(popupText)
        layout.add_widget(closeButton)       
        popup = Popup(title ='Error:', content=layout, size_hint=(.5, .25))  
        popup.open()
        closeButton.bind(on_release = popup.dismiss)

    def info_popup(self, error):
        layout = GridLayout(cols = 1, padding = 10, spacing=20)
        popupText = Label(text = error)
        closeButton = Button(text = "Acknowledge")
        layout.add_widget(popupText)
        layout.add_widget(closeButton)       
        popup = Popup(title ='Error:', content=layout, size_hint=(.5, .25))  
        popup.open()
        closeButton.bind(on_release = popup.dismiss) 

    def change_page(self, next_page):
            source = self.output_image.source
            source = source.split('-')
            if next_page:
                num = int(source[1][0])+1
            else:
                num = int(source[1][0])-1
            source[1] = f'{num}.jpg'
            source = '-'.join(source)
            if os.path.isfile(source):
                self.output_image.source = source
            else:
                pass

    def save_image(self, OBJECT):
        try:
            trg_path = self.file_path
            trg_path = trg_path.split('/')
            trg_path.pop(-1)
            trg_path = '/'.join(trg_path)
            name = trg_path.split('/')[-1].lower()
            trg_path = f'{trg_path}/{name}.pdf'
            shutil.copyfile('latex_output/latex_raw.pdf', trg_path)
            self.info_popup('Succesfully saved .PDF to parent folder')
        except OSError:
            self.info_popup('No Parent Folder Detected')

    def save(self, OBJECT):
        try:
            with open(self.file_path, 'w') as fout:
                fout.write(self.text_box.text)
        except FileNotFoundError:
            self.info_popup('No file selected or file does not exist')

    def load_view(self, OBJECT):
        popup_list = []
        layout = GridLayout(rows=2, padding=10, spacing=20)
        filechooser = FileChooserListView(path="projects")
        layout.add_widget(filechooser)
        button_layout = GridLayout(cols=3, padding=10, spacing=20, size_hint_y = .2)
        new_button = Button(text='New')
        button_layout.add_widget(new_button)
        select_button = Button(text='Select')
        button_layout.add_widget(select_button)
        exit_button = Button(text='Close')
        button_layout.add_widget(exit_button)
        layout.add_widget(button_layout)
        popup = Popup(title='New', content=layout, size_hint=(.75, .75))
        popup_list.append(popup)
        new_button.bind(on_release= lambda run: self.file_or_folder(filechooser.path, popup_list))
        select_button.bind(on_release=lambda run:self.load(filechooser.selection, popup_list))
        exit_button.bind(on_release=popup.dismiss)
        popup.open()

    def load(self, file_path, popup):
        popup[0].dismiss()
        try:
            self.file_path = file_path[0]
            with open(self.file_path) as fout:
                text = fout.read()
            self.text_box.text = text
            self.update_output(None)
        except UnicodeDecodeError:
            self.info_popup('Selected file is not a .TeX file')


    def file_or_folder(self, path, popup_list):
        layout = GridLayout(rows=2, padding=10, spacing=20)
        button_layout = GridLayout(cols=2, padding=10, spacing=20, size_hint_y = .2)
        folder_button = Button(text='Folder', on_release=lambda run: self.new_folder_name(path, popup_list))
        button_layout.add_widget(folder_button)
        file_button = Button(text='File', on_release=lambda run: self.new_file_name(path, popup_list))
        button_layout.add_widget(file_button)
        layout.add_widget(button_layout)
        popup = Popup(title='New', content=layout, size_hint=(.75, .75))
        popup_list.append(popup)
        popup.open()

    def new_folder_name(self, path, popup_list):
        layout = GridLayout(rows=2, padding=10, spacing=20)
        name = TextInput(hint_text='Enter Name Here')
        layout.add_widget(name)
        create_button = Button(text='Submit', on_release=lambda run: self.new_folder(path, name.text, popup_list))
        layout.add_widget(create_button)
        popup = Popup(title='Folder Name:', content=layout, size_hint=(.25, .25))
        popup.open()
        popup_list.append(popup)

    def new_file_name(self, path, popup_list):
        layout = GridLayout(rows=2, padding=10, spacing=20)
        name = TextInput(hint_text='Enter Name Here')
        layout.add_widget(name)
        create_button = Button(text='Submit', on_release=lambda run: self.new_file(path, name.text, popup_list))
        layout.add_widget(create_button)
        popup = Popup(title='File Name:', content=layout, size_hint=(.25, .25))
        popup.open()
        popup_list.append(popup)

    def new_folder(self, path, name, popup_list):
        for popup in popup_list:
            popup.dismiss()
        os.mkdir(f'{path}/{name}')
        close_button = Button(text='Done')
        popup = Popup(title='File Created', content=close_button, size_hint=(.25, .25))
        popup.open()
        close_button.bind(on_release=popup.dismiss)

    def new_file(self, path, name, popup_list):
        for popup in popup_list:
            popup.dismiss()
        f = open(f'{path}/{name}.TeX', 'w')
        f.write('\\documentclass[12pt]{article}\n\\begin{document}\n\nYour Work Here\n\n\\end{document}')
        close_button = Button(text='Done')
        popup = Popup(title='File Created', content=close_button, size_hint=(.25, .25))
        popup.open()
        close_button.bind(on_release=popup.dismiss)
  
if __name__ == '__main__':
    LaTeXEditorApp().run()

