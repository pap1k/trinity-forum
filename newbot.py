from bs4 import BeautifulSoup as bs
import requests, re, time, datetime, xmltodict, vk, sys, html, antiddos

LASTID = 0
PROCESSING = {}
DELAY = 240

def date(unixtime, format = '%d.%m.%Y %H:%M:%S'):
    d = datetime.datetime.fromtimestamp(unixtime)
    return d.strftime(format)

def log(text):
    print('['+date(time.time())+']: '+str(text))

def getAta4(subforums):
    for i in range(len(subforums)-1, 0, -1):
        title = subforums[i].lower()
        if "жалобы на хелперов" in title:
            return "ata4s/helper_report.jpg"
        elif "претензии к работе администраторов" in title:
            return "ata4s/admin_report.jpg"
        elif "на лидеров фракций, банд," in title:
            return "ata4s/leader_report.jpg"
        elif "новый лидер" in title:
            return "ata4s/new_leader.jpg"
        elif "банды" in title:
            return "ata4s/gang_news.jpg"
        elif "байкерские клубы" in title:
            return "ata4s/biker_news.jpg"
        elif "мафии" in title:
            return "ata4s/maf_news.jpg"
        elif "правительство" in title:
            return "ata4s/polit_news.jpg"
        elif "передачу постов" in title:
            return None
        elif "поощрения лидерам" in title:
            return None
        elif "выговоры лидеров" in title:
            return "ata4s/leader_reb.jpg"
    return "ata4s/fract_news.jpg"

class Forum:
    s = requests.Session()
    s.headers.update({'User-Agent': 'Grecko/1.0'})
    s.proxies = {'http': 'socks5h://127.0.0.1:9050','https': 'socks5h://127.0.0.1:9050'}
    def __init__(self):
        index = self.s.get('https://gta-trinity.ru/forum/').text
        log("Установлено подключение.")
        #if "REACTLABSPROTECTION" in index:
        ddos_code = antiddos.get(index)
        log("ddos code: "+ddos_code)
        cookies = dict(
            name='REACTLABSPROTECTION',
            value=ddos_code,
            path='/',
            domain='gta-trinity.ru',
            expires=2145916555,
            rest = {'hostOnly':True}
        )
        log("Установлен обход. Начинается парсинг.")
        self.s.cookies.set(**cookies)
    def html(self):
        return self.s.get("https://gta-trinity.ru:443/forum/index.php?/discover/8.xml/", timeout=20)

    def linkhtml(self, link):
        return self.s.get(link, timeout=20)
forum = Forum()
posted_ids = open("posts.txt", "r").read().split(",")
news_names = ['nyūsu', 'novedad', 'NOTIZIA', '𝐍𝐞𝐰𝐬', 'новост', 'ньюс', 'notizie', 'news','noticias', 'новый лидер', 'выговоры лидеров', 'жалобы на хелперов', 'претензии к работе администраторов', 'на лидеров фракций, банд,', 'передачу постов', 'поощрения лидерам и хелперам']
news_alerts = ['usa na]', 'pa$e news', 'usa news', 'news agency', 'rc news', 'usa:news','af news', 'us news', 'rc:news', 'новостное']

while True:
    try:
        ghtml = forum.html()
        #print(ghtml.text)
        if not ghtml:
            log("Форум сдох: "+str(ghtml))
            continue
        try:
            xml = xmltodict.parse(ghtml.text, encoding='utf-8')
        except:
            log("Не удалось спарсить XML. Переподключение...")
            forum = Forum()
            continue
        for post in xml['rss']['channel']['item']:

            post_id = re.findall(r't&comment=(\d+)', post['link'])[0]
            title = post['title']
            #log(title)

            HasTitle=False
            ExitFlag=False
            for news_alert in news_alerts:
                if not ExitFlag:
                    sub = title.lower().replace(news_alert, '')
                    if len(sub) != len(title): ExitFlag = True
            for news_name in news_names:
                if news_name.lower() in sub:
                    HasTitle = True
            if(not HasTitle): continue

            if str(post_id) in posted_ids:
                continue

            posted_ids.append(post_id)
            PROCESSING = {"id": post_id, "title": title}
            LASTID = post_id
            if len(posted_ids) >= 20:
                posted_ids = posted_ids[1:]
            open("posts.txt", "w").write(",".join(posted_ids))
            #choosing hashtag
            if "жалоб" in title.lower() or "претенз" in title.lower():
                tag = "#ccreport"
            else:
                tag = "#ccnews"

            attached_images = []
            index = bs(forum.linkhtml(post['link']).text,'html.parser')
            forum_post = index.find_all('div', class_='ipsColumn ipsColumn_fluid')[-1]
            forum_post = forum_post.find('div', class_='ipsType_normal ipsType_richText ipsContained')
            try:
                for img in forum_post.find_all('img'):
                    if not "emoji" in img['src']:
                        attached_images.append(img['src'])
            except: pass
            
            if len(attached_images) == 0:
                hat = None
                index = bs(forum.linkhtml(re.findall(r"(.+)\?do=findComment&", post['link'])[0]).text,'html.parser')

                forum_post = index.find_all('div', class_='ipsColumn ipsColumn_fluid')[0]
                forum_post = forum_post.find('div', class_='ipsType_normal ipsType_richText ipsContained')
                try: hat = forum_post.find_all('img')[0]['src']
                except: pass

            subforum = []
            nav_bar = index.find('nav', class_="ipsBreadcrumb ipsBreadcrumb_top ipsFaded_withHover")
            nav_bar = nav_bar.find('ul', attrs={"data-role": True})
            spans = nav_bar.find_all('span')
            for sp in spans:
                subforum.append(re.sub(r'(\<(/?[^>]+)>)', '', str(sp)))
            subforum.append(title)

            #sending post to vk
            #uploading photo(s)
            if len(attached_images) != 0:
                photo = ""
                for img in attached_images:
                    photo += vk.upload_photo(img) + ","
            elif hat:
                photo = vk.upload_photo(hat)
            else:
                photo = vk.upload_photo(getAta4(subforum))

            post['description'] = re.sub(r'\t', '', post['description'])
            post['description'] = re.sub(r'\n\s*\n', '\n', post['description'])
            post['description'] = html.unescape(post['description'])

            wall_post_data =  {
                    "owner_id": 0-vk.POST_GROUP_ID,
                    "from_group": 1,
                    "message": f"{tag}\n{title}\n\n{post['description']}",
                    "publish_date": int(time.time())+24*3600,
                    "copyright": post['link']
                }
            if photo: wall_post_data["attachments"] = photo,
            result = vk.vk_r("wall.post", wall_post_data)
            vk.vk_r("messages.send", {"peer_id": vk.PROD_CONV_PEER, "message": f"В отложке новый пост:\n\n{tag}\n{title}\n\n{post['link']}"})
            #vk.vk_r("messages.send", {"peer_id": 218999719, "message": f"В отложке новый пост:\n\n{tag}\n{title}\n\n{post['link']}"})
            
            print(":::::::::::::::::::::::::::::::::::::::")
            log("Posted \""+title+"\" post_id = "+str(post_id))
            print(":::::::::::::::::::::::::::::::::::::::\n")
        time.sleep(DELAY)
    except KeyboardInterrupt:
        print()
        log("ok")
        sys.exit(1)
    except requests.exceptions.RequestException as ex:
        try:
            if PROCESSING['id'] != LASTID:
                vk.vk_r("messages.send", {"peer_id": vk.PROD_CONV_PEER, "message": f"Произошла ошибка обратотки поста {PROCESSING['id']} в теме {PROCESSING['title']}, связанная с ошибкой подколчюения к форуму ({str(ex)}). Посмотрите вручную."})
        except KeyError:
            pass
        log("Request error: "+str(ex))
    except Exception as ex:
        log('Uncaught exception: '+str(ex))
    # except Exception as ex:
    #     open("lastheml.html", "w", encoding='utf-8').write(ghtml.text)
    #     forum = Forum()
    #     log("Необработанное исключение. Форум обновлен."+str(ex))
