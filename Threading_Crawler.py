from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from requests.adapters import Retry
from requests import Session
import json5
import time
from concurrent.futures import ThreadPoolExecutor
import re
import time
import requests
import os

start_time = time.time()
image_error_filename=""
review_error_filename=""
review_page_error_filename=""
place_page_error_filename=""
main_page_error_filename=""
record_filename=""
json_filename=""

done_filename="" 

k=0
main_url_list=[]
directory = ''
options = Options()
options.add_argument('--headless')

for n in range(21):
    main_url = f"https://en.tripadvisor.com.hk/Attractions-g294217-Activities-c47-oa{k}-Hong_Kong.html" 
    main_url_list.append(main_url)
    k+=30

def get_place_list(main_url:str):
        driver = webdriver.Chrome(options=options)
        driver.get(main_url)
        time.sleep(10)

        main_soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        main=main_soup.find("main")
        place_list=[]
        divs = main.find_all('div', attrs={'class': 'PFVlz'})
        for div in divs:
            for link in div.find_all('a', href=True):
                place_list.append("https://en.tripadvisor.com.hk/"+link['href'])
        return place_list

def get_review_links(count: int, place_url: str):
    review_list=[]
    count=0
    for n in range(5):
        if count==0:
            new_url=place_url
        else:
            index = place_url.find("Reviews")
            new_url=place_url[:index + len("Reviews")] + f"-or{count}" + place_url[index + len("Reviews"):]
        review_list.append(new_url)
        count+=10
    return review_list

def img_url_modifier(url:str):
    pattern = r"w=\d+"
    w_url = re.sub(pattern, "w=1200", url)
    pattern = r"h=\d+"
    new_url = re.sub(pattern, "h=1200", w_url)

    return new_url

def get_place_done_list(filename:str):
    with open(filename, 'r') as f:
        data =f.read()
        place_done_list=data.split(",")
    return place_done_list

def worker(main_url_list,driver):
            for main_url in main_url_list:
                print(main_url)
                try:
                    place_list=get_place_list(main_url)
                    #place_done_list=get_place_done_list(done_filename)
                    #place_list = [x for x in place_list if x not in place_done_list]
                    for place_url in place_list:
                        time.sleep(20)
                        try:
                            start=time.time()
                            print(place_url)

                            image_count=0
                            review_list=[]
                            _img_list=[]

                            #driver = webdriver.Chrome(options=options)
                            driver.get(place_url)
                            time.sleep(10)
                            place_soup = BeautifulSoup(driver.page_source, 'html.parser')
                            print("PLACE SOUP AVAILABLE")

                            name_element = place_soup.find('h1', {'class': 'biGQs _P fiohW eIegw', 'data-automation': 'mainH1'})
                            name = name_element.text

                            category_element = place_soup.find('div', {'class': 'fIrGe _T bgMZj'})
                            category = category_element.text

                            default_photos=place_soup.find('div',{"class":'yMdQy w'})
                            imgs = default_photos.find_all('img')
                            src_list = [img['src'] for img in imgs]
                            for src in src_list:
                                filename = f'{name}_{image_count}.jpg'
                                print(filename)
                                #time.sleep(10)
                                try:
                                    response = requests.get(src,timeout=60)
                                    with open(os.path.join(directory, filename), 'wb') as f:
                                        f.write(response.content)
                                    _img_list.append(filename)
                                    image_count+=1
                                except Exception as e:
                                    print(e)
                                    print(place_url)
                                    with open(image_error_filename, 'a') as file:
                                        file.write(place_url+",") 
                                    pass

                            popular_mention_list = place_soup.find('div', {'class': '_T UObru'})
                            if popular_mention_list !=None:
                                popular_mentions=set()
                                popular_elements = popular_mention_list.find_all('span')
                                for popular in popular_elements:
                                    popular_mentions.add(popular.text)
                                popular_mentions=list(popular_mentions)
                                data_dict={"name":name,"category":category,"popular_mentions":popular_mentions,"default_images":_img_list}

                            else:
                                data_dict={"name":name,"category":category,"default_images":_img_list}

                            count=0
                            review_url_list = get_review_links(count,place_url)
                            review_img_list=[]
                            draft_review_img_list=[]
                            main_place_name=name
                            review_dict={}
                            review_count=0

                            for review_url in review_url_list: 
                                print(review_url)
                                try:
                                    driver.get(review_url)
                                    time.sleep(5)
                                    updated_page_source = driver.page_source
                                    review_soup = BeautifulSoup(updated_page_source, 'html.parser')
                                    print("REVIEW SOUP AVAILABLE")
                                    reviews_html = review_soup.find('div', {'class': 'LbPSX'}) 
                                    reviews_html_list = reviews_html.find_all('div',{'class': 'C'})
                                    for review_html in reviews_html_list: #iterate through each review
                                        try:
                                            draft_review_img_list=[]
                                            review_img_list=[]

                                            review_names_finder = review_html.find_all('div', {'class': 'biGQs _P fiohW qWPrE ncFvv fOtGX'}) #review names
                                            for name in review_names_finder:
                                                if name!=None:
                                                    append_name= name.find('span',{'class': "yCeTE"}).text
                                                else:
                                                    append_name=main_place_name

                                            review_text_finder = review_html.find_all('div', {'class': "biGQs _P pZUbB KxBGd"}) #review names

                                            for text in review_text_finder:
                                                if text!=None:
                                                    append_text= text.find('span',{'class': "yCeTE"}).text
                                                else:
                                                    append_text="NONE"

                                            review_img_finder = review_html.find_all('div', {'class': 'LblVz _e q'})

                                            for img_element in review_img_finder:
                                                draft_review_img_list.append(img_element.find_all('img'))

                                            for imgs in draft_review_img_list:
                                                for img in imgs:
                                                    img_url= img.get('src')
                                                    img_url= img_url_modifier(img_url)
                                                    filename = f'{main_place_name}_{image_count}.jpg'
                                                    print(filename)
                                                    #time.sleep(5)
                                                    try:
                                                        response = requests.get(img_url,timeout=60)

                                                        with open(os.path.join(directory, filename), 'wb') as f:
                                                            f.write(response.content)
                                                        review_img_list.append(filename)
                                                        image_count+=1
                                                    except Exception as e:
                                                        print(e)
                                                        print(place_url)
                                                        with open(image_error_filename, 'a') as file:
                                                            file.write(place_url+",") 
                                                        pass


                                            new_row = {'topic': append_name, 'review': append_text, "photos":review_img_list}
                                            review_dict[f"review_{review_count}"]=new_row
                                            review_count+=1
                                        except Exception as e:
                                            print(e)
                                            print(review_url)
                                            with open(review_error_filename, 'a') as file:
                                                file.write(review_url+",") 
                                            pass
                                except Exception as e:
                                    print(e)
                                    print(review_url)
                                    with open(review_page_error_filename, 'a') as file:
                                        file.write(review_url+",") 
                                    pass
                            data_dict["reviews"]=review_dict
                            print(data_dict)
                            end=time.time()
                            print(f"Time Taken:{end-start}")

                            json_data = json5.dumps(data_dict, indent=2,ensure_ascii=False)
                            with open(json_filename, 'a') as file:
                                 file.write(json_data+",") 

                            with open(record_filename, 'a') as file:
                                 file.write(place_url+",")
                        except Exception as e:
                            print(e)
                            print(place_url)
                            with open(place_page_error_filename, 'a') as file:
                                file.write(place_url+",") 
                            pass
             
                except Exception as e:
                    print(e)
                    with open(main_page_error_filename, 'a') as file:
                        file.write(main_url+",") 
                    pass

def split_list(lst, n):
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

def setup_fx_driver():

    options = Options()
    options.add_argument('--headless')
 
    driver = webdriver.Chrome(options=options)

    return driver

def setup_workers(main_url_list):
    
    files = split_list(main_url_list,5)
    drivers = [setup_fx_driver() for _ in range(5)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(worker, files, drivers)

    [driver.quit() for driver in drivers]
    

start=time.time()
setup_workers(main_url_list)
end=time.time()