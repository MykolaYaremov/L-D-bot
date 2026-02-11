import requests

class Parser:

    def __init__(self, locale="uk_UA", per_page=10):
        self.url = "https://university.sigma.software/wp-json/su/v1/catalog"
        self.locale = locale
        self.per_page = per_page
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
    
    def fetch_page(self, page_number):
        params = self.default_params.copy()
        params['paged'] = page_number
        try:
            response = self.session.get(self.url, params=params)
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
    
    def parse(self):
        page = 0
        while True:
            courses_for_page = self.fetch_page(page)

            if not courses_for_page:
                break

            page += 1
            
            self.courses_list.extend(courses_for_page)
        return self.courses_list

            



        
