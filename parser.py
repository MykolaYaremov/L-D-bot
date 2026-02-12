import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time

class Parser:

    def __init__(self, locale="uk_UA", per_page=10):
        self.url_courses = "https://university.sigma.software/wp-json/su/v1/catalog"
        self.url_faq = "https://university.sigma.software/faq/"
        self.locale = locale
        self.per_page = per_page
        self.faq_cache_ttl = 3600  # кешування кожну годину
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.default_params = {
            "locale": locale,
            "paged": 0,
            "per_page": per_page,
            "type": "courses",
            "direction": "all"
        }
        self.courses_list = []
        self.faq_cache: Dict[str, Dict] = {}

    def fetch_page(self, page_number):
        params = self.default_params.copy()
        params['paged'] = page_number
        try:
            response = self.session.get(self.url_courses, params=params)
            if (response.status_code == 200):
                data_json = response.json()
                all_data = data_json.get('data')
                if (all_data):
                    courses = all_data.get('items', [])
                    return courses
            else:
                print(response.status_code)
        except(requests.ConnectionError):
            print("Connection error")

    def parse_courses(self):
        page = 0
        while True:
            courses_for_page = self.fetch_page(page)

            if not courses_for_page:
                break

            page += 1
            
            self.courses_list.extend(courses_for_page)
        return self.courses_list

    def parse_faq(self, url=None) -> List[Dict]:
        target_url = url if url else self.url_faq
        now = time.time()

        if target_url in self.faq_cache:
            cache_entry = self.faq_cache[target_url]
            if now - cache_entry["time"] < self.faq_cache_ttl:
                return cache_entry["data"]

        try:
            response = self.session.get(target_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            faq_container = soup.select_one('div.faq-items')
            if not faq_container:
                faq_container = soup

            faq_items = []
            questions = faq_container.find_all(["h2", "h3"])

            for q_tag in questions:
                question_text = q_tag.get_text(strip=True)
                if len(question_text) < 10:
                    continue

                answer_tag = q_tag.find_next_sibling(["div", "p", "ul", "ol"])
                if not answer_tag:
                    answer_tag = q_tag.parent.find_next_sibling(["div", "p"])

                if answer_tag:
                    answer_text = answer_tag.get_text(separator="\n", strip=True)
                    answer_text = " ".join(answer_text.split())
                else:
                    answer_text = "[відповідь не знайдено]"

                faq_items.append({
                    "question": question_text,
                    "answer": answer_text,
                })

            self.faq_cache[target_url] = {
                "time": now,
                "data": faq_items
            }
            return faq_items

        except Exception as e:
            print(f"Помилка при парсингу FAQ: {e}")
            return []