import datetime
import time
import dateparser
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class FIDO(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, web_driver: WebDriver, max_count_documents: int = None,
                 last_document: S3PDocument = None, num_scrolls: int = 25):
        super().__init__(refer, plugin, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)


    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter")

        # Должно быть два конфига: файловый и нативный
        # categories = {'FIDO News Center': 'https://fidoalliance.org/content/fido-news-center/',   - NATIVE
        #
        #               'FIDO Case Studies': 'https://fidoalliance.org/content/case-study/',        - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)
        #
        #               'FIDO In the News': 'https://fidoalliance.org/content/fido-in-the-news/',   - NATIVE
        #                       (нужно переходить к прикрепленным ссылкам и сохранять оттуда весь контент, а в аннотацию
        #                         то, что было написано на странице FIDO, заголовок тоже с FIDO)
        #
        #               'FIDO Presentations': 'https://fidoalliance.org/content/presentation/',     - NATIVE
        #
        #               'FIDO White Papers': 'https://fidoalliance.org/content/white-paper/'}       - FILE
        #                       (заголовок и аннотация со страницы FIDO, а текст из файла)

        for category in self.CATEGORIES:

            self._driver.get(self.CATEGORIES[category])

            scroll_counter = 0

            try:
                time.sleep(3)

                self.close_popup()
                doc_table = self._driver.find_elements(By.XPATH, '//li[contains(@class,\'card-products\')]')
                last_doc_table_len = len(doc_table)

                while True:
                    # Scroll down to bottom
                    self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    scroll_counter += 1
                    # self.logger.info(f"counter = {counter}")

                    # Wait to load page
                    time.sleep(3)

                    self.close_popup()

                    self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(1)

                    doc_table = self._driver.find_elements(By.XPATH, '//li[contains(@class,\'card-products\')]')
                    new_doc_table_len = len(doc_table)
                    if last_doc_table_len == new_doc_table_len:
                        break
                    if scroll_counter > self.NUM_SCROLLS:
                        flag = False
                        break

            except Exception as e:
                self.logger.debug('Не удалось найти scroll')
                break

            self.logger.debug(f'Обработка списка элементов ({len(doc_table)})...')

            for doc in doc_table:
                doc_link = doc.find_element(By.XPATH, './/h2/a').get_attribute('href')

                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])

                self._driver.get(doc_link)
                self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.wp-block-post-title')))

                self.logger.debug(f'Entered: {doc_link}')

                title = self._driver.find_element(By.XPATH, "//h1[contains(@class,'wp-block-post-title\')]").text

                pub_date = dateparser.parse(
                    self._driver.find_element(By.XPATH, "//h1[contains(@class,'wp-block-post-title')]/../..//time").text)

                if self.SOURCE_TYPE == 'NATIVE':

                    text_content = self._driver.find_element(By.XPATH,
                                                            "//div[contains(@class,'wp-block-post-content')]").text

                    abstract = None

                    web_link = doc_link

                    other_data = {'category': category}

                elif self.SOURCE_TYPE == 'FILE':

                    try:
                        abstract = self._driver.find_element(By.XPATH,
                                                            "//div[contains(@class,'wp-block-post-content')]").text
                        web_link = self._driver.find_element(By.XPATH,
                                                            "//div[@class='wp-block-button']/a").get_attribute('href')
                        text_content = None

                        other_data = {'category': category, 'fido_link': doc_link}

                    except:
                        web_link = doc_link
                        abstract = None
                        text_content = self._driver.find_element(By.XPATH,
                                                                "//div[contains(@class,'wp-block-post-content')]").text

                        other_data = {'category': category}

                else:
                    self.logger.info('Неизвестный тип источника SOURCE_TYPE')
                    raise ValueError('source_type must be a type of source: "FILE" or "NATIVE"')

                doc = S3PDocument(None,
                                   title,
                                   abstract,
                                   text_content,
                                   web_link,
                                   None,
                                   other_data,
                                   pub_date,
                                   datetime.now())

                self.find_document(doc)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])

    def close_popup(self):

        try:
            # close_btn = self._driver.find_element(By.XPATH, "//span[@class = 'hustle-icon-close']")
            close_btn = self._driver.find_element(By.XPATH, "//button[contains(@class,'hustle-button-close')]")
            try:
                close_btn.click()
            except Exception as e:
                self.logger.debug(f"Can't click the close button in popup with Exception: {e}")
        except:
            self.logger.debug('Popup not found')

