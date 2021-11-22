import requests, random

USER_ACCESS = ""
VK_API_V = "5.103"
POST_GROUP_ID = 145098987
POST_GROUP_ID_TEST = 200575367
TEST_CONV_PEER = 184 + 2000000000
PROD_CONV_PEER = 166 + 2000000000

class Image:
    img = ""
    def __init__(self, img):
        self.img = img
    def content(self):
        if "http" in self.img:
            return requests.get(self.img, stream=True).content
        else: return open(self.img, 'rb')
        

def vk_r(method, params = {}, token = USER_ACCESS):
    add_params = {"v": VK_API_V, "access_token": token}
    if method == "messages.send": add_params['random_id'] = random.randint(0, 10000)
    data = {**params, **add_params}
    r = requests.post("https://api.vk.com/method/"+method, data=data).json()
    if 'error' in r: return None
    else: return r['response']

def upload_photo(img):
    if not img: return None
    img = Image(img)
    r = vk_r("photos.getWallUploadServer", {"peer_id": POST_GROUP_ID})
    r = requests.post(r['upload_url'],files={'photo':('photo.png', img.content(),'image/png')}).json()
    r = vk_r("photos.saveWallPhoto", {"photo": r['photo'], "server": r['server'], "hash": r['hash']})
    return f"photo{r[0]['owner_id']}_{r[0]['id']}" if r else ""


