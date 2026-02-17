import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import time


class Parser:
    def __init__(self, locale="uk_UA", per_page=10):
        self.url_courses = "https://university.sigma.software/wp-json/su/v1/catalog"
        self.url_faq = "https://university.sigma.software/faq/"
        self.locale = locale
        self.per_page = per_page

        # НАЛАШТУВАННЯ КЕШУ
        self.faq_cache_ttl = 3600  # FAQ живе 1 годину
        self.courses_cache_ttl = 86400  # Курси живуть 24 години (86400 сек)

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
        self.courses_last_update = 0  # Час останнього оновлення курсів
        self.faq_cache: Dict[str, Dict] = {}

    def fetch_page(self, page_number: int) -> List[Dict[str, Any]]:
        """Завантажує одну сторінку курсів з API."""
        params = self.default_params.copy()
        params['paged'] = page_number
        try:
            response = self.session.get(self.url_courses, params=params, timeout=10)
            if response.status_code == 200:
                data_json = response.json()
                all_data = data_json.get('data')
                if all_data:
                    return all_data.get('items', [])
            else:
                print(f"API Error: Status {response.status_code}")
        except requests.ConnectionError:
            print("Connection error while fetching courses")
        except Exception as e:
            print(f"Error fetching page {page_number}: {e}")
        return []

    def parse_courses(self) -> List[Dict[str, Any]]:
        """
        Парсить курси.
        Якщо дані вже є і пройшло менше 24 годин — повертає збережену копію.
        """
        now = time.time()

        # ПЕРЕВІРКА: Якщо дані є і вони "свіжі" (менше 24 год), не чіпаємо сайт
        if self.courses_list and (now - self.courses_last_update < self.courses_cache_ttl):
            return self.courses_list

        # Якщо даних немає або вони старі — завантажуємо наново
        print("🔄 Починаю оновлення списку курсів (24h expired)...")
        new_courses_list = []
        page = 0

        while True:
            courses_for_page = self.fetch_page(page)
            if not courses_for_page:
                break
            new_courses_list.extend(courses_for_page)
            page += 1

        if new_courses_list:
            self.courses_list = new_courses_list
            self.courses_last_update = now
            print(f"✅ Список оновлено. Завантажено курсів: {len(self.courses_list)}")
        else:
            print("⚠️ Не вдалося оновити курси, використовую старі дані.")

        return self.courses_list

    def parse_faq(self, url: Optional[str] = None) -> List[Dict[str, str]]:
        # (Цей метод залишається без змін, як у попередній версії)
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
            if not faq_container: faq_container = soup
            faq_items = []
            questions = faq_container.find_all(["h2", "h3"])
            for q_tag in questions:
                question_text = q_tag.get_text(strip=True)
                if len(question_text) < 5: continue
                answer_tag = q_tag.find_next_sibling(["div", "p", "ul", "ol"])
                if not answer_tag: answer_tag = q_tag.parent.find_next_sibling(["div", "p"])
                if answer_tag:
                    answer_text = answer_tag.get_text(separator="\n", strip=True)
                    answer_text = " ".join(answer_text.split())
                else:
                    answer_text = "Детальніше за посиланням."
                faq_items.append({"question": question_text, "answer": answer_text})
            self.faq_cache[target_url] = {"time": now, "data": faq_items}
            return faq_items
        except Exception as e:
            print(f"Помилка при парсингу FAQ: {e}")
            return []