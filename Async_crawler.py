from bs4 import BeautifulSoup as bs
import urllib.request
import os
import asyncio
import aiohttp
from aiohttp import ClientSession
import nest_asyncio
import json5
from urllib.parse import urlparse

output_json_filename=""
districts=["hong-kong-island","kowloon","new-territories","outlying-islands"]
#langs=["en","tc","sc"]
urls_list=[]
for district in districts:
        district_url=f'https://www.amo.gov.hk/en/historic-buildings/monuments/{district}/'
        data = urllib.request.urlopen(district_url).read()
        soup = bs(data)
        body=soup.find("body")
        for link in body.find_all('a', href=True):
            if "historic-buildings" in link["href"]:
                url="https://www.amo.gov.hk/"+str(link['href'])
                urls_list.append(url)

async def fetch(session, url):
    async with session.get(url) as response:
        text = await response.text()
        await do_something(session,response,url)

async def do_something(session,response,url):
    text = await response.text()
    url_soup=bs(text,"html.parser")

    data_dict={}

    name=url_soup.find("h2").get_text()
    descriptions= url_soup.find("p").get_text()
    location= url_soup.find("div", {"class": "locate"}).get_text()

    parsed_url = urlparse(url)
    path_components = parsed_url.path.split("/")
    monument_id=path_components[-2]

    count=0
    
    filename_dict={}
    for link in url_soup.find_all('a', href=True):
        link=link["href"]
        if link.endswith(".jpg")|link.endswith(".JPG"):
            count+=1
            directory = ''
            filename = f'{name}_{count}.jpg'
            
            pic_url="https://www.amo.gov.hk"+link
            async with session.get(pic_url) as img_response:
                img_data = await img_response.content.read()
                with open(os.path.join(directory, filename), 'wb') as f:
                    f.write(img_data)
                filename_dict[count]=filename
                print(filename)
                count+=1

            print('Image saved as', filename)

    data_dict={"monument_id":monument_id,"name":name,"descriptions":descriptions,"location":location,"photos":filename_dict}

    json_data = json5.dumps(data_dict, indent=2,ensure_ascii=False)
    with open(output_json_filename, 'a') as file:
        file.write(json_data+",") 

async def main():
    urls_queue = asyncio.Queue()
    crawled_urls = set()

    for url in urls_list:
        await urls_queue.put(url)

    async with aiohttp.ClientSession() as session:
        async_list = []
        while not urls_queue.empty():
            url = await urls_queue.get()
            if url in crawled_urls:
                continue

            else:
                action_item = fetch(session, url)
                async_list.append(action_item)
                crawled_urls.add(url)

        results = await asyncio.gather(*async_list)
        print(results)

#nest_asyncio.apply()
asyncio.run(main())