import time

import undetected_chromedriver
from parser import Parser
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import random
counter = 0

class YandexParser:
    def __init__(self, id_yandex: int):
        """
        @param id_yandex: ID Яндекс компании
        """
        self.id_yandex = id_yandex

    def __open_page(self):
        url: str = 'https://yandex.ru/maps/org/{}/reviews/'.format(str(self.id_yandex))
        opts = undetected_chromedriver.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('headless')
        opts.add_argument('--disable-gpu')
        driver = undetected_chromedriver.Chrome(options=opts)
        parser = Parser(driver)
        driver.get(url)
        return parser
    def __scroll_to_bottom(self, elem, driver) -> None:
        """
        Скроллим список до последнего отзыва
        :param elem: Последний отзыв в списке
        :param driver: Драйвер undetected_chromedriver
        :return: None
        """
        driver.execute_script(
            "arguments[0].scrollIntoView();",
            elem
        )
        time.sleep(1)
        new_elem = driver.find_elements(By.XPATH, '//a')[-1]
        if elem == new_elem:
            return
        self.__scroll_to_bottom(new_elem, driver)

    def parse_user_data(self, url):
        opts = undetected_chromedriver.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('headless')
        opts.add_argument('--disable-gpu')
        driver = undetected_chromedriver.Chrome(options=opts)
        driver.get(url)
        time.sleep(4)
        #chain = ActionChains(driver)
        #print(driver.find_elements(By.XPATH, 'a[contains(@class, "Link_dark")]'), driver.find_elements(By.XPATH, 'a[contains(@class, "Link_dark")]')[-1])
        scroll_elem = driver.find_elements(By.XPATH, '//a')[-1]
        self.__scroll_to_bottom(scroll_elem, driver)
        links_elem = driver.find_elements(By.XPATH, '//a[contains(@class, "Link_dark")]')
        links = [elem.get_attribute('href') for elem in links_elem]
        driver.close()
        return links



    def parse(self, type_parse: str = 'default') -> dict:
        """
        Функция получения данных в виде
        @param type_parse: Тип данных, принимает значения:
            default - получает все данные по аккаунту
            company - получает данные по компании
            reviews - получает данные по отчетам
        @return: Данные по запрошенному типу
        """
        result:dict = {}
        page = self.__open_page()
        time.sleep(4)
        try:
            if type_parse == 'default':
                result = page.parse_all_data()
            if type_parse == 'company':
                result = page.parse_company_info()
            if type_parse == 'reviews':
                result = page.parse_reviews()

        except Exception as e:
            print(e)
            return result
        finally:
            page.driver.close()
            page.driver.quit()
            return result

    def save_reviews(self, reviews):
        global counter
        try:
            print(reviews["error"])
            return
        except:
            pass
        #print(reviews)
        #print()
        rew = [[reviews['company_reviews'][i]['stars'],reviews['company_reviews'][i]['name']]+list(reviews['company_info'].values()) for i in range(len(reviews['company_reviews'])) if reviews['company_reviews'][i]['stars'] != None]
        df = pd.DataFrame(rew)
        df.to_csv(f'./data/reviews{counter}.csv', index=False, header=False)
        counter+=1

    def save_checkoints(self, was, all_ids):
        df_was = pd.DataFrame(was)
        df_all_ids = pd.DataFrame(all_ids)
        df_was.to_csv('./checkpoints.csv', index=False, header=False)
        df_all_ids.to_csv('./all_ids.csv', index=False, header=False)


    def read_checkpoints(self):
        df_was = pd.read_csv('./checkpoints.csv')
        df_all_ids = pd.read_csv('./all_ids.csv')
        was = df_was['was'].tolist()
        all_ids = df_all_ids['all_ids'].tolist()
        return was, all_ids
    def prepare(self, elem):

        #print(elem)
        if isinstance(elem, str):
            try:
                return int(elem)
            except:
                return int(elem.split('/')[-1])
        else:
            return elem

    def parse_infinity(self, id_start= None, start_from_checkpoint=False):
        user_links_save = []
        if start_from_checkpoint:
            was, all_ids = self.read_checkpoints()
        else:
            all_ids = [id_start]
            was = []

        while True:
            try:
                for id in all_ids:
                    #print(all_ids)
                    #print(id, self.prepare(id))
                    id = self.prepare(id)
                    self.id_yandex = id
                    #print(id)
                    if id in was:
                        time.sleep(10)

                        all_ids.remove(id)
                        continue
                    was.append(id)
                    #all_ids.remove(id)

                    reviews = self.parse()
                    try:
                        print(reviews['error'])
                        continue
                    except:
                        pass
                    self.save_reviews(reviews)
                    print(1)
                    #print(reviews['company_reviews'])
                    user_links = [i['name_link'] for i in reviews['company_reviews']]
                    #print(user_links)
                    user_links_save += user_links[0:5]
                    try:
                        print(self.parse_user_data(user_links[random.randint(0, len(user_links) - 1)]), user_links[random.randint(0, len(user_links) - 1)])
                        counter = 0
                        while True:
                            ids_new = self.parse_user_data(user_links[random.randint(0, len(user_links) - 1)])
                            if len(ids_new) > 10:
                                break
                            counter += 1
                            if counter > 100:
                                raise Exception

                        all_ids = ids_new+all_ids
                    except Exception as e:
                        counter = 0
                        while True:
                            print(user_links)
                            ids_new = self.parse_user_data(user_links[random.randint(0, len(user_links) - 1)])
                            if len(ids_new) > 10:
                                break
                            counter += 1
                            if counter > 100:
                                print('We are in infinite loop')
                    self.save_checkoints(was, all_ids)
            except Exception as e:
                print(e)
                break



