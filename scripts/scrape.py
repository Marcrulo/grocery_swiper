# IMPORTS
import requests
import bs4
import time
from PIL import Image
import io
import pandas as pd
import os
import cloudinary


# EXTRACT WEB CONTENT
url = 'https://www.tilbudsugen.dk/partner/netto-114?page=100'
response = requests.get(url)
time.sleep(2)
if response.status_code == 200:
    print("Request was successful.")
else:
    assert False, f"Request failed with status code {response.status_code}"
soup = bs4.BeautifulSoup(response.text, 'html.parser')

# GET PRODUCT IDS
links = soup.find_all('a', href=True)
product_links = [link['href'] for link in links if link['href'].startswith('https://www.tilbudsugen.dk/single/')]
all_ids = [int(link.split('/')[-1]) for link in product_links]

# GET PRODUCT INFO
products = {}
all_ids = all_ids
N = len(all_ids)
for i, data_id in enumerate(all_ids):
    if i % 10 == 0:
        print(f"Processing #{i} of {N}")
    data_url = f"https://www.tilbudsugen.dk/_next/data/0LbXUdvz48Lb0tgkd4pVT/dk/single/{data_id}.json?id={data_id}"
    response = requests.get(data_url)
    time.sleep(1)
    if response.status_code != 200:
        assert False, f"Request failed with status code {response.status_code}"
    page_props = response.json()['pageProps']
    
    price        = page_props['offer']['price']
    brand        = page_props['offer']['brand']['name']
    category     = page_props['offer']['productVariant']['category']['name']
    product_name = page_props['offer']['productName']['productName']
    units        = page_props['offer']['units']
    quantity     = int(eval(page_props['offer']['quantity']))
    unit_type    = page_props['offer']['unitType']
    store_name   = page_props['offer']['chain']['name']
    image_url    = page_props['offer']['imageUrl']
    start_date   = page_props['offer']['startDate']
    end_date     = page_props['offer']['endDate']

    products[data_id] = [price, brand, category, product_name, units, quantity, unit_type, store_name, image_url, start_date, end_date]

# GATHER DATA IN TABLE
df_products = pd.DataFrame.from_dict(products, orient='index', columns=['price', 'brand', 'category', 'product_name', 'units', 'quantity', 'unit_type', 'store_name', 'image_url', 'start_date', 'end_date'])
df_products.reset_index(inplace=True)
df_products.rename(columns={'index': 'data_id'}, inplace=True)
date = df_products['start_date'].mode()[0]
df_products.to_csv(f'../data/csv/products_{date}.csv', index=False)


# DOWNLOAD RESIZED IMAGES
def download_and_resize_image(image_url, data_id, date):
    extension = image_url.split("?")[0].split(".")[-1].lower()
    os.makedirs(f"/tmp/imgs/{date}", exist_ok=True)
    filename = f"/tmp/imgs/{date}/{data_id}.{extension}"

    resp = requests.get(image_url)
    if resp.status_code != 200:
        print("Failed to download image:", resp.status_code)
    else:
        img = Image.open(io.BytesIO(resp.content))
        w, h = img.size
        max_side = max(w, h)
        if max_side > 300:
            scale = 300 / max_side
            new_size = (int(round(w * scale)), int(round(h * scale)))
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS
            img = img.resize(new_size, resample)
        img.save(filename)
for idx, row in df_products.iterrows():
    download_and_resize_image(row['image_url'], row['data_id'], date)


# UPLOAD IMAGES TO CLOUDINARY
API_SECRET = os.getenv("CLOUDINARY_KEY")
cloudinary.config( 
    cloud_name = "dfqzmnlga", 
    api_key    = "733583949868714", 
    api_secret = API_SECRET,
    secure=True
)

# GO THROUGH ALL NEW IMAGES AND UPLOAD TO CLOUDINARY
# upload_result = cloudinary.uploader.upload("../data/imgs/2025-10-25/10738668.jpg", public_id=f"10738668", asset_folder=date)
for idx, row in df_products.iterrows():
    data_id = row['data_id']
    extension = row['image_url'].split("?")[0].split(".")[-1].lower()
    local_path = f"/tmp/imgs/{date}/{data_id}.{extension}"
    public_id = f"{data_id}"
    try:
        upload_result = cloudinary.uploader.upload(local_path, public_id=public_id, folder=date)
        print(f"Uploaded image for data_id {data_id} to Cloudinary.")
    except Exception as e:
        print(f"Failed to upload image for data_id {data_id}: {e}")