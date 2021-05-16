import time
import pathlib

import PIL
import yaml
import os

from PIL import Image
from jinja2 import Environment, PackageLoader, select_autoescape
from datetime import datetime
from lxml import html
from collections import OrderedDict

env = Environment(
    loader=PackageLoader('project', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


def read_consts_from_yaml():
    with open('consts.yaml', 'r') as f:
        return yaml.safe_load(f)


def create_url(tag):
    translation_table = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
    return tag.replace(" ", "-").lower().translate(translation_table)


def create_new_article():
    def get_article_inputs():
        print("article title:  ", end=" ")
        article_title = input()
        print("article tags(seperate with comma ','):  ", end=" ")
        article_tags = input()
        print("article description:  ", end=" ")
        article_description = input()
        print("article keywords(seperate with comma ','):  ", end=" ")
        article_keywords = input()
        return article_title, article_tags, article_description, article_keywords

    def create_file_and_path(article_title):
        year, month, day = time.strftime("%Y %m %d").split()
        pathlib.Path(
            pathlib.Path(__file__).parent.parent / year / month / day / create_url(article_title) / "assets").mkdir(
            parents=True, exist_ok=True)
        # pathlib.Path(pathlib.Path(__file__).parent.parent / year / month / day / article_title / "index.html").touch()
        return pathlib.Path(
            pathlib.Path(__file__).parent.parent / year / month / day / create_url(article_title) / "index.html")

    def build_page(template_name, context, output_name):
        template = env.get_template(template_name)
        page = template.render(context)
        # export page
        with open(output_name, "w", encoding='UTF-8') as file:
            file.write(page)

    article_title, article_tags, article_description, article_keywords = get_article_inputs()
    index_path = create_file_and_path(article_title)
    consts = read_consts_from_yaml()
    year, month, day = time.strftime("%Y %m %d").split()
    context = {
        'main': {
            'username': consts["user_name"],
            'title': consts["main_title"],
            'description': consts["main_description"],
            'keywords': consts["main_keywords"],
            'language': consts["main_language"],
            'favicon': consts["main_favicon"],
            'cover_image': consts["main_cover_image"],
            'github': consts["main_github"]
        },
        'title': article_title,
        'tags': [{'name': ' '.join(tag.split()), 'url': create_url(' '.join(tag.split()))} for tag in
                 article_tags.split(",")],
        'description': article_description,
        'keywords': article_keywords,
        'updated_time': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        'date': year + "/" + month + "/" + day
    }
    # print(context)
    build_page('article.html', context, index_path)
    build_web_site()


def build_web_site():
    def getAllHtmlFilePaths(dirName):
        listOfFile = os.listdir(dirName)
        allFiles = list()
        for entry in listOfFile:
            if entry in ["static_generator", "tags"]:
                continue
            fullPath = os.path.join(dirName, entry)
            if os.path.isdir(fullPath):
                allFiles = allFiles + getAllHtmlFilePaths(fullPath)
            else:
                if fullPath.split(".")[-1] == "html" and os.path.splitext(pathlib.Path(fullPath).parent)[0] != \
                        os.path.splitext(pathlib.Path(__file__).parent.parent)[0]:
                    allFiles.append(fullPath)
        return allFiles

    def get_datas_from_htmls(html_file_paths):
        def parse_html(file_path):
            file_content = open(file_path, mode='r', encoding='UTF-8').read()
            tree = html.fromstring(file_content)

            title_xpath = "/html/body/div/article/header/h1/text()"
            title = tree.xpath(title_xpath)[0]

            date_xpath = "/html/body/div/article/header/div/div[1]/time/text()"
            date = tree.xpath(date_xpath)[0]

            datetime_xpath = " /html/body/div/article/header/div/div[1]/time/@datetime"
            datetime = tree.xpath(datetime_xpath)[0]

            tag_span_xpath = "/html/body/div/article/header/div/div[2]/span"
            tags = []
            for tag in tree.xpath(tag_span_xpath)[0]:
                tags.append(tag.text_content())
            return {"title": title, "date": date, "datetime": datetime, "tags": tags}

        data_list = []
        for file_path in html_file_paths:
            _temp = parse_html(file_path)
            path_parts = os.path.normpath(file_path).split(os.sep)
            _temp["hyperlink"] = "/".join(path_parts[-5:])
            data_list.append(_temp)
        return sorted(data_list, key=lambda k: k['datetime'], reverse=True)

    def get_tag_datas(data_list):
        tags = set()
        for data in data_list:
            for tag in data["tags"]:
                tags.add(tag)

        tag_list = []
        for tag in tags:
            tag_url = create_url(tag) + ".html"
            _temp = {"tag": tag, "tag_url": tag_url}
            tag_list.append(_temp)

        return sorted(tag_list, key=lambda k: k['tag'])

    def get_writings(data_list):
        writing_dict = {}

        def is_year_in_writing_list(year):
            if year in writing_dict:
                return True
            return False

        for data in data_list:
            year = data["date"].split("/")[0]
            if is_year_in_writing_list(year):
                writing_dict[year].append(data)
            else:
                writing_dict[year] = [data]

        return OrderedDict(writing_dict)

    def get_tag_pages(data_list):
        tag_pages = {}

        def is_tag_in_tag_list(tag):
            if tag in tag_pages:
                return True
            return False

        for data in data_list:
            for tag in data["tags"]:
                if is_tag_in_tag_list(tag):
                    tag_pages[tag].append({'title': data["title"], "date": data["date"], "datetime": data["datetime"],
                                           "hyperlink": data["hyperlink"]})
                else:
                    tag_pages[tag] = [{'title': data["title"], "date": data["date"], "datetime": data["datetime"],
                                       "hyperlink": data["hyperlink"]}]

        return tag_pages

    def build_page(template_name, context, output_name):
        template = env.get_template(template_name)
        page = template.render(context)
        # export page
        with open(output_name, "w", encoding='UTF-8') as file:
            file.write(page)

    def build_tag_pages(template_name, context, tag_pages, output_folder):
        temp_writing_dict = {}

        def is_year_in_writing_list(year):
            if year in temp_writing_dict:
                return True
            return False

        for tag in tag_pages:
            temp_writing_dict = {}
            tag_url = create_url(tag) + ".html"
            for data in tag_pages[tag]:
                year = data["date"].split("/")[0]
                if is_year_in_writing_list(year):
                    temp_writing_dict[year].append(data)
                else:
                    temp_writing_dict[year] = [data]
            new_context = {
                'main': context['main'],
                'tag_name': tag,
                'tag_url': tag_url,
                'writings': temp_writing_dict
            }
            build_page(template_name, new_context, output_folder / tag_url)

    html_file_paths = getAllHtmlFilePaths(pathlib.Path(__file__).parent.parent)
    data_list = get_datas_from_htmls(html_file_paths)
    tag_list = get_tag_datas(data_list)
    writings = get_writings(data_list)
    tag_pages = get_tag_pages(data_list)
    consts = read_consts_from_yaml()
    context = {
        'main': {
            'username': consts["user_name"],
            'title': consts["main_title"],
            'description': consts["main_description"],
            'keywords': consts["main_keywords"],
            'language': consts["main_language"],
            'favicon': consts["main_favicon"],
            'cover_image': consts["main_cover_image"],
            'github': consts["main_github"]
        },
        'data_list': data_list,
        'tag_list': tag_list,
        'writings': writings
    }
    build_page('index.html', context, pathlib.Path(pathlib.Path(__file__).parent.parent / "index.html"))
    build_page('writing.html', context, pathlib.Path(pathlib.Path(__file__).parent.parent / "writing.html"))

    pathlib.Path(pathlib.Path(__file__).parent.parent / "tags").mkdir(parents=True, exist_ok=True)
    build_tag_pages("tag.html", context, tag_pages, pathlib.Path(pathlib.Path(__file__).parent.parent / "tags"))


def image_compress():
    def getAllImagePaths(dirName, extension_list=('jpg', 'jpeg', 'png')):
        listOfFile = os.listdir(dirName)
        allFiles = list()
        for entry in listOfFile:
            fullPath = os.path.join(dirName, entry)
            if os.path.isdir(fullPath):
                allFiles = allFiles + getAllImagePaths(fullPath)
            else:
                if fullPath.split(".")[-1] in extension_list and os.path.splitext(pathlib.Path(fullPath).parent)[0] != \
                        os.path.splitext(pathlib.Path(__file__).parent.parent)[0]:
                    allFiles.append(fullPath)
        return allFiles

    def resizeWidthOfImage(path, max_width=512):
        extension = path.split('.')[-1].lower()
        if extension == 'png':
            # convert it to RBG color palette
            image = Image.open(path).convert('RGB')
            width_percent = max_width / float(image.size[0])
            new_height_size = int(float(image.size[1]) * width_percent)
            # change extension
            path = '.'.join(path.split('.')[:-1]) + '.jpg'
        elif extension in ['jpeg', 'jpg']:
            image = Image.open(path)
            # calculate ratio for calculating height
            width_percent = max_width / float(image.size[0])
            new_height_size = int(float(image.size[1]) * width_percent)
        else:
            return False
        image = image.resize((max_width, new_height_size), PIL.Image.NEAREST)
        image.save(path)

    image_list = getAllImagePaths(pathlib.Path(__file__).parent.parent)
    for image in image_list:
        resizeWidthOfImage(image)


def push_to_github():
    pass


def menu():
    print("1 --- CREATE NEW ARTICLE ")
    print("2 --- BUILD WEB SITE ")
    print("3---- IMAGE COMPRESS")
    print("4---- PUSH TO GITHUB")
    choice = input()
    if choice not in ("1", "2", "3", "4"):
        print("NOT VALID,  CHOOSE AGAIN")
        return menu()
    return choice


def main():
    choice = menu()
    if choice == "1":
        create_new_article()
    elif choice == "2":
        build_web_site()
    elif choice == "3":
        image_compress()
    elif choice == "4":
        push_to_github()


if __name__ == "__main__":
    main()
