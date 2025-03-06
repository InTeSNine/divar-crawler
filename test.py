import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
from datetime import datetime
import time

# تنظیمات
CONFIG = {
    'SEEN_ADS_FILE': 'seen_ads.json',
    'OUTPUT_FILE': 'new_ads.txt',
    'SEARCH_URLS': [
        'https://divar.ir/s/tehran/transport-delivery-jobs?q=%D8%A7%D8%B3%D9%86%D9%BE%20%D8%A8%D8%A7%DA%A9%D8%B3',
        'https://divar.ir/s/tehran/transport-delivery-jobs?q=%D9%BE%DB%8C%DA%A9%20%D9%85%D9%88%D8%AA%D9%88%D8%B1%DB%8C%20%D9%85%DB%8C%D8%A7%D8%B1%D9%87',
        'https://divar.ir/s/tehran/transport-delivery-jobs?q=%D9%BE%DB%8C%DA%A9%20%D9%85%D9%88%D8%AA%D9%88%D8%B1%DB%8C%20%D8%A7%D8%B3%D9%86%D9%BE'
    ],
    'HEADERS': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'REQUEST_DELAY': 3,
    'MAX_ADS': 5
}

def load_seen_ads():
    """بارگذاری لیست آگهی‌های پردازش شده"""
    try:
        if os.path.exists(CONFIG['SEEN_ADS_FILE']):
            with open(CONFIG['SEEN_ADS_FILE'], 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f'❌ خطا در بارگذاری لیست آگهی‌ها: {e}')
        return []

def save_seen_ads(seen_ads):
    """ذخیره لیست آگهی‌های پردازش شده"""
    try:
        with open(CONFIG['SEEN_ADS_FILE'], 'w') as f:
            json.dump(seen_ads, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'❌ خطا در ذخیره لیست آگهی‌ها: {e}')

def get_ad_links(url):
    """استخراج لینک‌های آگهی از صفحه جستجو"""
    try:
        response = requests.get(url, headers=CONFIG['HEADERS'])
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        for card in soup.select('a.kt-post-card__action'):
            relative_link = card.get('href')
            if relative_link:
                absolute_link = urljoin('https://divar.ir', relative_link)
                links.append(absolute_link)
        
        return links[:CONFIG['MAX_ADS']]
    
    except Exception as e:
        print(f'❌ خطا در دریافت لینک‌ها از {url}: {e}')
        return []

def scrape_ad_page(ad_url):
    """استخراج جزئیات از صفحه آگهی"""
    try:
        time.sleep(CONFIG['REQUEST_DELAY'])
        response = requests.get(ad_url, headers=CONFIG['HEADERS'])
        soup = BeautifulSoup(response.text, 'html.parser')

        # استخراج عنوان با هندلینگ خطا
        title = "عنوان یافت نشد"
        try:
            title_element = soup.find('h1', class_='kt-page-title__title')
            if title_element:
                title = title_element.text.strip()
        except AttributeError:
            pass

        # استخراج توضیحات با هندلینگ خطا
        description = "توضیحات یافت نشد"
        try:
            description_div = soup.find('div', class_='kt-description-row')
            if description_div:
                description_p = description_div.find('p', class_='kt-description-row__text--primary')
                if description_p:
                    description = '\n'.join(
                        [line.strip() 
                         for line in description_p.text.split('\n') 
                         if line.strip()]
                    )
        except AttributeError:
            pass

        # استخراج ID
        ad_id = ad_url.split('/')[-1]

        return {
            'id': ad_id,
            'title': title,
            'description': description,
            'link': ad_url
        }

    except Exception as e:
        print(f'❌ خطا در پردازش آگهی {ad_url}: {e}')
        return None

def save_results(ads):
    """ذخیره نتایج در فایل متنی"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CONFIG['OUTPUT_FILE'], 'w', encoding='utf-8') as f:
            f.write(f"=== آگهی‌های جدید ({timestamp}) ===\n\n")
            for idx, ad in enumerate(ads, 1):
                f.write(f"آگهی #{idx}\n")
                f.write(f"عنوان: {ad['title']}\n")
                f.write(f"توضیحات:\n{ad['description']}\n")
                f.write(f"لینک: {ad['link']}\n")
                f.write("-"*50 + "\n\n")
        print(f'✅ نتایج در {CONFIG["OUTPUT_FILE"]} ذخیره شد')
    except Exception as e:
        print(f'❌ خطا در ذخیره نتایج: {e}')

def main():
    seen_ads = load_seen_ads()
    new_ads = []

    # جمع‌آوری لینک‌ها
    all_links = []
    for url in CONFIG['SEARCH_URLS']:
        print(f'🔎 در حال بررسی آدرس: {url}')
        links = get_ad_links(url)
        all_links.extend(links)
        print(f'📎 تعداد لینک‌های یافت شده: {len(links)}')

    # پردازش آگهی‌ها
    for link in all_links:
        ad_id = link.split('/')[-1]
        
        if ad_id in seen_ads:
            print(f'⏩ آگهی {ad_id} قبلاً پردازش شده')
            continue
            
        print(f'🔄 در حال پردازش آگهی: {link}')
        ad_data = scrape_ad_page(link)
        
        if ad_data:
            new_ads.append(ad_data)
            seen_ads.append(ad_id)
            print(f'✔️ آگهی {ad_id} با موفقیت پردازش شد')

    # ذخیره نتایج
    if new_ads:
        save_results(new_ads)
        save_seen_ads(seen_ads)
        print(f'\n🎉 تعداد آگهی‌های جدید: {len(new_ads)}')
    else:
        print('\n⚠️ هیچ آگهی جدیدی یافت نشد')

if __name__ == '__main__':
    main()