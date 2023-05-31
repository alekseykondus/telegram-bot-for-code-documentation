# -*- coding: utf-8 -*-
"""GraduateWork.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rC3Yglv3K_ZJXabWNWRnkPxBtfgbxLpg
"""

!pip
install
openai > null
!pip
install
ast_comments > null
!pip3
install
pytelegrambotapi > null
!pip
install
giturlparse > null
!apt - get
install
doxygen > null
!pip
install
doxypypy > null
!pip
install
pydrive > null

import os
import re
import ast
import ssl
import sys
import time
import openai
import shutil
import requests
import subprocess
import giturlparse
import ast_comments as astcom
from google.colab import drive
from openai.error import RateLimitError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from contextlib import redirect_stdout
from google.colab import auth
from oauth2client.client import GoogleCredentials


class GoogleDriveManager:
    _instance = None

    @staticmethod
    def get_instance():
        if not GoogleDriveManager._instance:
            GoogleDriveManager()
        return GoogleDriveManager._instance

    def __init__(self):
        if GoogleDriveManager._instance:
            raise Exception("This class is a singleton. Use get_instance() method to get an instance.")
        else:
            drive.mount("/content/drive", force_remount=True)
            auth.authenticate_user()
            self.gauth = GoogleAuth()
            self.gauth.credentials = GoogleCredentials.get_application_default()
            self.drive = GoogleDrive(self.gauth)
            self.pathToDrive = '/content/drive/MyDrive'
            GoogleDriveManager._instance = self

    def get_path_to_drive(self):
        return self.pathToDrive

    def print_files(self, directory):
        files = self.get_files_in_directory(directory)
        for filename in files:
            print(filename)

    def get_files_in_directory(self, directory):
        files = []
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if self.is_directory(path) and not self.is_ignored_directory(path):
                files.extend(self.get_files_in_directory(path))
            elif self.is_python_file(filename):
                files.append(path)
        return files

    def is_directory(self, path):
        return os.path.isdir(path)

    def is_ignored_directory(self, path):
        ignored_directories = ['.git', '.idea']
        return os.path.basename(path) in ignored_directories

    def is_python_file(self, filename):
        return os.path.splitext(filename)[1] == ".py"

    def get_file_id_from_file_list(self, file_path, file_list):
        for file in file_list:
            if file['title'] == file_path.split('/')[-1]:
                return file['id']
        return ''

    def get_file_id_from_path(self, file_path, codeOrDoc):
        repo_name = os.path.basename(file_path)
        file_id = ''
        file_list = self.get_root_file_list()

        if codeOrDoc == "doc":
            folder_name = "docs"
            docs_folder = self.get_folder_by_name(file_list, folder_name)
            if docs_folder:
                docs_folder_id = docs_folder['id']
                file_list = self.drive.ListFile({'q': f"'{docs_folder_id}' in parents and trashed=false"}).GetList()
                file_id = self.get_file_id_from_file_list(file_path, file_list)
            else:
                print(f"Folder {folder_name} not found")
        elif codeOrDoc == "code":
            file_id = self.get_file_id_from_file_list(file_path, file_list)
        else:
            raise Exception("codeOrDoc can only be \"code\" or \"doc\"")

        if file_id == '':
            raise Exception("File id " + repo_name + " was not found")
        return file_id

    def create_archive(self, folder_path, codeOrDoc):
        repo_name = os.path.basename(folder_path)
        zip_file_path = self.create_zip_file(repo_name, codeOrDoc)
        if not self.check_zip_file(zip_file_path):
            return False, zip_file_path
        return True, zip_file_path

    def get_download_link(self, folder_path, codeOrDoc):
        repo_name = os.path.basename(folder_path)
        success_create_zip, file_path = self.create_archive(folder_path, codeOrDoc)
        if not success_create_zip:
            time.sleep(1)
            success_create_zip, file_path = self.create_archive(folder_path, codeOrDoc)
        MAX_ATTEMPTS = 50
        ATTEMPT_DELAY = 1
        attempt = 1
        file_id = ''
        while True:
            try:
                file_id = self.get_file_id_from_path(file_path, codeOrDoc)
            except Exception as e:
                self.handle_error(e)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(ATTEMPT_DELAY)
                    attempt += 1
                    continue
                else:
                    print(
                        f"The maximum number of attempts to execute the process {ATTEMPT_DELAY} has been reached. Completion of work.")
                    break
            else:
                break
        self.insert_permission(file_id)
        link_to_archive = 'https://drive.google.com/file/d/' + file_id
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        return link_to_archive, download_link

    def authenticate(self):
        auth.authenticate_user()

    def get_root_file_list(self):
        return self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

    def get_folder_by_name(self, file_list, folder_name):
        for folder in file_list:
            if folder['mimeType'] == 'application/vnd.google-apps.folder' and folder['title'] == folder_name:
                return folder
        return None

    def insert_permission(self, file_id):
        file = self.get_drive_file(file_id)
        return file.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'
        })

    def create_zip_file(self, repo_name, codeOrDoc):
        if codeOrDoc == "code":
            os.system(f"cd /content/drive/MyDrive && zip -r -q '{repo_name}'.zip '{repo_name}'")
            return "/content/drive/MyDrive/" + repo_name + ".zip"
        elif codeOrDoc == "doc":
            os.system(f"cd /content/drive/MyDrive/docs && zip -r -q '{repo_name}'.zip '{repo_name}'")
            return "/content/drive/MyDrive/docs/" + repo_name + ".zip"
        else:
            raise Exception("codeOrDoc can only be \"code\" or \"doc\"")

    def check_zip_file(self, zip_path):
        return os.path.exists(zip_path)

    def handle_error(self, exception):
        print(f"An error has occurred: {exception}")

    def get_drive_file(self, file_id):
        return self.drive.CreateFile({'id': file_id})


class DocumentationGenerator:
    def __init__(self, language, api_key):
        self.language = language
        openai.api_key = api_key
        self.total_tokens = 0
        self.ignored_dirs = ['.git',
                             '.idea',
                             '__pycache__',
                             'venv',
                             '.vscode',
                             'dist',
                             'build',
                             '*.pyc',
                             '*.pyo',
                             '*.pyd',
                             '*.pyz',
                             '*.pyw',
                             '*.egg-info',
                             '*.egg',
                             '*.dist-info']

    def get_api_key(self):
        return openai.api_key

    def get_total_tokens(self):
        return self.total_tokens

    def get_ignored_dirs(self):
        return self.ignored_dirs

    def generate_docs(self, code):
        prompt = self._get_prompt(code)
        message = [{"role": "user", "content": prompt}]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=2048,
            temperature=1.2,
            messages=message
        )
        self.total_tokens += response['usage']['total_tokens']
        answer = response['choices'][0]['message']['content']
        return answer.strip()

    def _get_prompt(self, code):
        # if self.language == "Java":
        #    return "You task is to write Javadoc for a given code block. I need to document a function, class, module. Write me a docstring that describes what the function, class, module does, what parameters it accepts and returns, and what exceptions may occur during its execution. Also, please make sure that the documentation complies with the Javadoc standards. The code should not be modified, only the docstrings should be added. Once the docstring is added, please send me the updated code block with the new documentation.. For the following Python code:\n\n" + str(code) + "\n\nYou must return the result as code, DON'T DELETE a single line of code"
        if self.language == "Python":
            return "You task is to write docstrings for a given code block. I need to document a function, class, module. Write me a docstring that describes what the function, class, module does, what parameters it accepts and returns, and what exceptions may occur during its execution. Also, please make sure that the documentation complies with the PEP 257 standards. The code should not be modified, only the docstrings should be added. Once the docstring is added, please send me the updated code block with the new documentation.. For the following Python code:\n\n" + str(
                code) + "\n\nYou must return the result as code, DON'T DELETE a single line of code"

    def is_method(self, function_node, ast_tree):
        return isinstance(function_node.parent, ast.ClassDef)

    def generate_docs_for_block_and_change_node(self, tree, node, debug=False):
        try:
            code_with_docs = self.generate_docs(ast.unparse(node))
        except RateLimitError:
            print("Rate limit exceeded. Waiting for 20 seconds...")
            time.sleep(21)
            code_with_docs = self.generate_docs(ast.unparse(node))

        result = code_with_docs
        if debug:
            print(result)
            print(
                "----------------------------------------------------------------------------------------------------------------------------")

        old_node_index = tree.body.index(node)
        try:
            tree.body[old_node_index] = astcom.parse(result)
        except SyntaxError as e:
            print(f"Syntax error: {e}")
            print("Repeated demand")
            self.generate_docs_for_block_and_change_node(tree, node, debug)

    def generate_docs_for_code_from_file(self, file_path, debug=False):
        with open(file_path, 'r') as file:
            source_code = file.read()

        tree = astcom.parse(source_code, type_comments=True)

        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node

        if debug:
            code_block = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if debug:
                    code_block.append(node)
                self.generate_docs_for_block_and_change_node(tree, node, debug)
            elif isinstance(node, ast.FunctionDef) and not self.is_method(node, tree):
                if debug:
                    code_block.append(node)
                self.generate_docs_for_block_and_change_node(tree, node, debug)

        new_source_code = astcom.unparse(tree)
        with open(file_path, 'w') as f:
            f.write(new_source_code)

    def is_ignored_directory(self, directory_name):
        return directory_name in self.ignored_dirs

    def generate_docs_for_code_from_dir(self, dir_path):
        for filename in os.listdir(dir_path):
            path = os.path.join(dir_path, filename)
            if os.path.isdir(path):
                directory_name = os.path.basename(path)
                if self.is_ignored_directory(directory_name):
                    continue
                self.generate_docs_for_code_from_dir(path)
            if self.language == "Python":
                if os.path.splitext(filename)[1] == ".py":
                    print(path)
                    self.generate_docs_for_code_from_file(str(path), debug=False)
            elif self.language == "Java":
                if os.path.splitext(filename)[1] == ".java":
                    print(path)
                    self.generate_docs_for_code_from_file(str(path), debug=False)


class DoxygenGenerator:
    def generate_Doxyfile(self, path, excluded_dirs):
        with open('Doxyfile', 'w') as file:
            file.write('PROJECT_NAME = "Example"\n')
            file.write('INPUT = ' + str(path) + '\n')
            file.write('RECURSIVE = YES\n')
            file.write('GENERATE_HTML = YES\n')
            file.write('GENERATE_HTML = YES\n')
            file.write('EXCLUDE = ' + ' \\\n'.join(excluded_dirs) + '\n')
            if not os.path.exists('/content/drive/MyDrive/docs/'):
                os.makedirs('/content/drive/MyDrive/docs/')
            if not os.path.exists('/content/drive/MyDrive/docs/' + os.path.basename(path)):
                os.makedirs('/content/drive/MyDrive/docs/' + os.path.basename(path))
            if os.path.isdir(path):
                file.write('HTML_OUTPUT = /content/drive/MyDrive/docs/' + os.path.basename(path) + '/html/' + '\n')
                file.write('LATEX_OUTPUT = /content/drive/MyDrive/docs/' + os.path.basename(path) + '/latex/' + '\n')
            elif os.path.isfile(path):
                if not os.path.exists(os.path.splitext(path)[0]):
                    os.makedirs(os.path.splitext(path)[0])
                file.write('HTML_OUTPUT = /content/drive/MyDrive/docs/' + os.path.splitext(path)[0] + '/html/' + '\n')
                file.write('LATEX_OUTPUT = /content/drive/MyDrive/docs/' + os.path.splitext(path)[0] + '/latex/' + '\n')
            file.write('EXTRACT_ALL = YES\n')
            file.write('echo "FILTER_PATTERNS = *.py=doxypypy"\n')

    def generate_doxygen_documentation(self, path, excluded_dirs):
        self.generate_Doxyfile(path, excluded_dirs)
        os.system('doxygen Doxyfile')


class GitManager:
    _instance = None

    @staticmethod
    def get_instance():
        if not GitManager._instance:
            GitManager()
        return GitManager._instance

    def __init__(self):
        if GitManager._instance:
            raise Exception("This class is a singleton. Use get_instance() method to get an instance.")
        else:
            GitManager._instance = self
            self.url = ''
            self.repo_name = ''
            self.localPathToDir = ''
            self.localPathToDocsDir = ''

    def get_ulr(self):
        return self.url

    def get_repo_name(self):
        return self.repo_name

    def get_local_path_to_code_dir(self):
        return self.localPathToCodeDir

    def get_local_path_to_docs_dir(self):
        return self.localPathToDocsDir

    @staticmethod
    def is_git_repo(text):
        try:
            url = giturlparse.parse(text)
            return url.resource == 'github.com' or url.resource == 'gitlab.com'
        except:
            return False

    def set_git_repo(self, text):
        url = giturlparse.parse(text)
        if self.is_git_repo(text):
            self.url = text
            self.repo_name = url.repo
            return True
        else:
            return False

    def clone(self, pathToDir):
        if self.get_repo_name() != '':
            url = self.url
            command = f'git clone {url} {pathToDir}/{self.repo_name}'
            if os.path.exists(f'{pathToDir}/{self.repo_name}'):
                shutil.rmtree(f'{pathToDir}/{self.repo_name}')
            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                print("Repository cloned successfully")
            except subprocess.CalledProcessError as e:
                print("Error while cloning repository")
                raise Exception(e.output.decode('utf-8'))
            self.localPathToCodeDir = f'{pathToDir}/{self.repo_name}'
            self.localPathToDocsDir = f'{pathToDir}/docs/{self.repo_name}'
            return True
        else:
            return False

    def extract_owner_and_repo(self, url):
        if "github.com" in url:
            parts = url.split("/")
            owner = parts[-2]
            repo = os.path.basename(url).replace('.git', '')
            return owner, repo
        elif "gitlab.com" in url:
            parts = url.split("/")
            owner = parts[-2]
            repo = os.path.basename(url).replace('.git', '')
            return owner, repo

        raise Exception("unable to find owner or name of repo")

    def get_repo_languages(self, url=None):
        if url is None:
            url = self.url
        owner, repo = self.extract_owner_and_repo(url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("response status_code not equale 200")

    def repo_contains_python_code(self, url=None):
        if url is None:
            url = self.url
        repo_data = self.get_repo_languages(url)
        # most_used_language = max(repo_data, key=repo_data.get)
        return 'Python' in repo_data


def get_usage_cost(api_key):
    openai.api_key = api_key
    r = openai.api_requestor.APIRequestor();
    import datetime

    today = datetime.date.today()
    start_date = today.strftime("%Y-%m-%d")
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    end_date = tomorrow.strftime("%Y-%m-%d")

    resp = r.request("GET", f'/dashboard/billing/usage?start_date={start_date}&end_date={end_date}')
    daily_costs = resp[0].data['daily_costs']
    line_items = daily_costs[0]['line_items']
    cost = next(item['cost'] for item in line_items if item['name'] == 'Chat models')
    return cost  # поверне в центах


import telebot
from telebot import types


class CodeDocumentationBot:
    def __init__(self, token, chat_gpt_api_key):
        self.bot = telebot.TeleBot(token)
        self.git_manager = GitManager.get_instance()
        self.drive_manager = GoogleDriveManager.get_instance()
        self.doxygen_generator = DoxygenGenerator()
        self.doc_generator = DocumentationGenerator(language='Python', api_key=chat_gpt_api_key)
        self.chat_gpt_api_key = chat_gpt_api_key

    def start(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Start Code Documentation")
            markup.add(btn1)
            self.bot.send_message(message.from_user.id, "👋 Hello! I'm your code documentation assistant bot!",
                                  reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            try:
                if message.text == 'Start Code Documentation':
                    self.bot.send_message(message.from_user.id, 'Submit a link to the github repository 🔗',
                                          parse_mode='Markdown')
                elif self.git_manager.is_git_repo(message.text):
                    self.doc_generator = DocumentationGenerator(language='Python', api_key=self.chat_gpt_api_key)
                    start_cost = get_usage_cost(self.doc_generator.get_api_key())
                    start_time = time.time()
                    print(message.from_user.id)
                    self.process_handler(message.text, message.from_user.id)
                    end_time = time.time()
                    end_cost = get_usage_cost(self.doc_generator.get_api_key())
                    execution_time = end_time - start_time
                    documentation_cost = end_cost - start_cost
                    print("Час виконання: ", execution_time, "секунд")
                    print("Кількість використаних токенів: ", self.doc_generator.get_total_tokens())
                    print("Документування коштувало: ", documentation_cost, "центів")
                else:
                    self.bot.send_message(message.from_user.id, 'Please send a link to the github repository\n',
                                          parse_mode='Markdown')
            except Exception as e:
                print(e)

        self.bot.polling(none_stop=True, interval=0)

    def process_handler(self, repository_link, user_id):
        try:
            self.git_manager.set_git_repo(repository_link)
            if not self.git_manager.repo_contains_python_code(repository_link):
                self.bot.send_message(user_id, 'I can only document Python code. The repository has no Python code\n',
                                      parse_mode='Markdown')
                return
            self.git_manager.clone(pathToDir=self.drive_manager.get_path_to_drive())
        except Exception as e:
            self.bot.send_message(user_id, 'Check if the link is correct\n', parse_mode='Markdown')
            raise e
        self.generate_code_documentation(user_id)
        self.generate_doxygen_documentation(user_id)
        if not os.path.exists(self.git_manager.get_local_path_to_docs_dir()):
            self.doxygen_generator.generate_doxygen_documentation(self.git_manager.get_local_path_to_code_dir())

    def generate_code_documentation(self, user_id):
        self.doc_generator.generate_docs_for_code_from_dir(self.git_manager.get_local_path_to_code_dir())
        try:
            link_to_archive_code, download_link_code = self.drive_manager.get_download_link(
                self.git_manager.get_local_path_to_code_dir(), codeOrDoc='code')
        except Exception as e:
            link_to_archive_code, download_link_code = self.drive_manager.get_download_link(
                self.git_manager.get_local_path_to_code_dir(), codeOrDoc='code')
        self.bot.send_message(user_id,
                              'You can see the folder with the documented code at the ' + f'[link]({link_to_archive_code})\n',
                              parse_mode='Markdown')
        print("link_to_archive_code: ", link_to_archive_code)

    def generate_doxygen_documentation(self, user_id):
        self.doxygen_generator.generate_doxygen_documentation(self.git_manager.get_local_path_to_code_dir(),
                                                              self.doc_generator.get_ignored_dirs())
        if not os.path.exists(self.git_manager.get_local_path_to_docs_dir()):
            self.doxygen_generator.generate_doxygen_documentation(self.git_manager.get_local_path_to_code_dir(),
                                                                  self.doc_generator.get_ignored_dirs())
        try:
            link_to_archive_doc, download_link_doc = self.drive_manager.get_download_link(
                self.git_manager.get_local_path_to_docs_dir(), codeOrDoc='doc')
        except Exception as e:
            link_to_archive_doc, download_link_doc = self.drive_manager.get_download_link(
                self.git_manager.get_local_path_to_docs_dir(), codeOrDoc='doc')
        self.bot.send_message(user_id,
                              'You can view the documentation folder by the ' + f'[link]({link_to_archive_doc})\n',
                              parse_mode='Markdown')
        print("link_to_archive_doc: ", link_to_archive_doc)


bot_token = '5970697110:AAH_cr4t-2Le3qBannP98IE6w1vXfx0wABU'
chat_gpt_api_key = "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"
with open('logs.txt', 'w') as file:
    with redirect_stdout(file):
        bot = CodeDocumentationBot(bot_token, chat_gpt_api_key)
        bot.start()
