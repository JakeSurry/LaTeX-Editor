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
import re
import os
import subprocess

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
        self.save_button = Button(text='Save')
        self.save_button.bind(on_release=self.save)
        self.side_menu.add_widget(self.save_button)
        self.load_button = Button(text='Load')
        self.load_button.bind(on_release=self.load_view)
        self.side_menu.add_widget(self.load_button)

        self.main_layout.add_widget(self.side_menu)

        self.text_box = self.text_input = TextInput(text='\\documentclass[12pt]{article}\n\\begin{document}\n\nExample\n\n\\end{document}', font_name='courier')
        self.text_box.bind(text = self.keywords)
        self.main_layout.add_widget(self.text_box)

        self.center_menu = GridLayout(rows=3, cols=1, size_hint_x = .15)
        self.main_layout.add_widget(self.center_menu)
        self.zoomin_button = Button(text='+', size_hint_y = .1)
        self.zoomin_button.bind(on_release = self.zoomin)
        self.center_menu.add_widget(self.zoomin_button)
        self.zoomout_button = Button(text='-', size_hint_y = .1)
        self.zoomout_button.bind(on_release = self.zoomout)
        self.center_menu.add_widget(self.zoomout_button)
        self.run_button = Button(text='Run')
        self.run_button.bind(on_release = self.update_output)
        self.center_menu.add_widget(self.run_button)

        self.output_scroll = ScrollView()
        self.image_size = 1000
        self.output_image = Image(source = 'latex_output/latex_raw1.png', size_hint=(None, None), size=(self.image_size,self.image_size), allow_stretch = True)
        self.output_scroll.add_widget(self.output_image)
        self.main_layout.add_widget(self.output_scroll)

        self.file_path = ''

        self.update_output(None)

        Window.size = (1440, 900)
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
        self.image_size += 50
        self.output_image.size = [self.image_size, self.image_size]
    def zoomout(self, OBJECT):
        self.image_size -= 50
        self.output_image.size = [self.image_size, self.image_size]
    def update_output(self, OBJECT):
        #self.output.text = self.text_box.text
        with open('latex_output/latex_raw.TeX', 'w') as fout:
            fout.write(self.text_box.text)
        r = subprocess.run(['/Library/TeX/texbin/latex', '-output-format=dvi', '-interaction=nonstopmode', 'latex_raw.TeX'], cwd='latex_output', capture_output = True)
        r2 = subprocess.run(['/Library/TeX/texbin/dvipng', 'latex_raw.dvi'], cwd='latex_output', capture_output = True)

        error = str(r.stdout).split('\\n')
        '''
        if len(error) > 14:
            self.error_popup(error)
        '''
        self.output_image.reload()

    def save(self, OBJECT):
        try:
            with open(self.file_path, 'w') as fout:
                fout.write(self.text_box.text)
        except FileNotFoundError:
            layout = GridLayout(cols = 1, padding = 10, spacing=20)
            popupText = Label(text = 'No file selected or File does not exist')
            closeButton = Button(text = "Acknowledge")
            layout.add_widget(popupText)
            layout.add_widget(closeButton)       
            popup = Popup(title ='Error:', content=layout, size_hint=(.5, .25))  
            popup.open()
            closeButton.bind(on_release = popup.dismiss) 

    def load_view(self, OBJECT):
        popup_list = []
        layout = GridLayout(rows=2, padding=10, spacing=20)
        filechooser = FileChooserListView(path="projects", on_submit=self.load)
        layout.add_widget(filechooser)
        button_layout = GridLayout(cols=2, padding=10, spacing=20, size_hint_y = .2)
        new_button = Button(text='New')
        button_layout.add_widget(new_button)
        exit_button = Button(text='Close')
        button_layout.add_widget(exit_button)
        layout.add_widget(button_layout)
        popup = Popup(title='New', content=layout, size_hint=(.75, .75))
        popup_list.append(popup)
        new_button.bind(on_release= lambda run: self.file_or_folder(filechooser.path, popup_list))
        exit_button.bind(on_release=popup.dismiss)
        popup.open()

    def load(self, OBJECT, file_path, pos):
        self.file_path = file_path[0]
        with open(self.file_path) as fout:
            text = fout.read()
        self.text_box.text = text
        self.update_output(None)

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
        close_button = Button(text='Ok')
        popup = Popup(title='Done', content=close_button, size_hint=(.25, .25))
        popup.open()
        close_button.bind(on_release=popup.dismiss)

    def new_file(self, path, name, popup_list):
        for popup in popup_list:
            popup.dismiss()
        f = open(f'{path}/{name}.TeX', 'w')
        f.write('\\documentclass[12pt]{article}\n\\begin{document}\n\nExample\n\n\\end{document}')
        close_button = Button(text='Ok')
        popup = Popup(title='Done', content=close_button, size_hint=(.25, .25))
        popup.open()
        close_button.bind(on_release=popup.dismiss)

    def error_popup(self, error):
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
  
if __name__ == '__main__':
    LaTeXEditorApp().run()

