# Walmart-Scrapy

#### Utilizando Scrapy para extrair dados do Walmart
#### Site: www.walmart.com.br/

#### Tutorial


```
$ rethinkdb
$ git clone https://github.com/wellington16/PontoFrio-Scrapy
$ pip install -r requirements.txt
$ cd PontoFrio-Scrapy
$ scrapy crawl wal -o resultado.json -t json
``` 

#### Índice
  * [Objetivos](https://github.com/wellington16/Walmart-Scrapy/blob/master/README.md#objetivos)
  * Arquivos:
      * [pontoFrio.py](https://github.com/wellington16/Walmart-Scrapy/blob/master/walmart/spiders/wal.py)
      * [pipelines.py](https://github.com/wellington16/Walmart-Scrapy/blob/master/walmart/pipelines.py)
      * [settings.py](https://github.com/wellington16/Walmart-Scrapy/blob/master/walmart/settings.py)
      * [items.py](https://github.com/wellington16/Walmart-Scrapy/blob/master/walmart/items.py)
  * [Tempo gasto](https://github.com/wellington16/Walmart-Scrapy/blob/master/README.md#tempo-gasto)
  * [Programas utilizados](https://github.com/wellington16/Walmart-Scrapy/blob/master/README.md#programas-utilizados)
  * [Referências](https://github.com/wellington16/Walmart-Scrapy/blob/master/README.md#referências)


#### Objetivos
- [x] Utilização de ```xpath``` nas buscas por links
- [x] Persistência das informações (Para persistir foi usado RethinkDB,MongoDB e PostgreSQL, mas como padrão o RethinkDB)
- [x] Submissão de formulários
- [x] Manipulação de querystrings
- [x] Tratamento de paginação
- [x] Utilização de logs para sinalizar ocorrências durante o scraping


#### Arquivo: [pontoFrio.py](https://github.com/wellington16/PontoFrio-Scrapy/blob/master/pontofrio/spiders/spider-pontoFrio.py)
```python 
# # -*- coding: utf-8 -*-
import scrapy

from walmart.items import WalmartItem
import logging


class WalmartSpider(scrapy.Spider):
    name = "wal"

    def start_requests(self):
        urls = [
            'https://www.walmart.com.br/categoria/informatica/computadores-e-all-in-one/?fq=C:4699/4702&utmi_p=wm-desktop/header&utmi_cp=linkheader_informatica_computadores_pos-4'
        ]
        for url in urls:
            logging.info(url)
            yield scrapy.Request(url=url, callback=self.parse)



    def parse(self, response):
        # logging.info('ACESSANDO URL: %s' % response.url)

        pages = response.xpath(
            '//*[@id="product-list"]/section/ul/li/section/a/@href'
            ).extract()
        for page_item in pages:
            next_item = response.urljoin(page_item)
            # logging.info(next_item)

            yield scrapy.Request(url=next_item,callback=self.parse_detail)

        next_page = response.xpath('//*[@id="product-list"]/a/@href').extract()
        start = 0
        for urls in next_page:
            try:
                next_url = scrapy.Request(url = urls.extract()[start],callback=self.parse)
                start += 1
                yield next_url

            except:
                logging.error("Game Over.")

    def parse_detail(self,response):

        item = WalmartItem()
        item['name'] = response.xpath('//*[@id="buybox"]/div/header/div/h1/text()').extract_first()
        item['precoAtual'] = response.xpath(
            '//*[@id="buybox"]/div/div[2]/div/div/div[1]/ul/li[1]/div[3]/div/p/span[@class="product-price-sell"]//text()'
        ).extract()
        # item['fotos'] = response.xpath('//*[@id="wm-pictures-carousel"]/div[1]/div/div/a/img[@class]/@src').extract()
        item['precoAntigo'] = response.xpath('//ul/li[1]/div[3]/div/p/span[@class="product-price-old"]//text()').extract_first()
        item['avaliacoes'] = response.xpath('//*[@id="rating"]/span/a/text()').extract_first()
        item['url'] = response.url
        yield item
```

#### Arquivo: [pipelines.py](https://github.com/wellington16/PontoFrio-Scrapy/blob/master/pontofrio/pipelines.py)
```python
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import rethinkdb as r

class WalmartPipeline(object):
    conn = None
    rethinkdb_settings = {}

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        rethinkdb_settings = settings.get('RETHINKDB', {})

        return cls(rethinkdb_settings)

    def __init__(self, rethinkdb_settings):
        self.rethinkdb_settings = rethinkdb_settings

    def open_spider(self, spider):
        if self.rethinkdb_settings:
            self.table_name = self.rethinkdb_settings.pop('table_name')
            self.db_name = self.rethinkdb_settings['db']
            self.conn = r.connect(**self.rethinkdb_settings)
            table_list = r.db(self.db_name).table_list().run(
                self.conn
            )
            if self.table_name not in table_list:
                r.db(self.db_name).table_create(self.table_name).run(self.conn)

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        if self.conn:
            r.table(self.table_name).insert(item).run(self.conn)
        return item

```

#### Arquivo: [settings.py](https://github.com/wellington16/PontoFrio-Scrapy/blob/master/pontofrio/settings.py)
```python
# -*- coding: utf-8 -*-

# Scrapy settings for walmart project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'walmart'

SPIDER_MODULES = ['walmart.spiders']
NEWSPIDER_MODULE = 'walmart.spiders'
DOWNLOAD_HANDLERS = {'s3': None}
DOWNLOADER_MIDDLEWARES = {'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None}
RETHINKDB = {'table_name': 'items', 'db': 'walmart'}
ITEM_PIPELINES = {'walmart.pipelines.WalmartPipeline': 1}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'walmart (+http://www.yourdomain.com)'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS=32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY=3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN=16
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
#COOKIES_ENABLED=False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'walmart.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'walmart.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'walmart.pipelines.SomePipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
#AUTOTHROTTLE_ENABLED=True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED=True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'

```

#### Arquivo: [items.py](https://github.com/wellington16/PontoFrio-Scrapy/blob/master/pontofrio/items.py)
```python
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class PontofrioItem(scrapy.Item):
    name = scrapy.Field()
    precoAtual = scrapy.Field()
    url = scrapy.Field()
    precoAntigo = scrapy.Field()
    avaliacoes = scrapy.Field()
    fotos= scrapy.Field()


```
#### Tempo gasto
  * Estudando: 3
  * Implementando: 1
  * Ajustando: 1
	

#### Programas utilizados
  * [XPath Helper](https://chrome.google.com/webstore/detail/xpath-helper/hgimnogjllphhhkhlmebbmlgjoejdpjl)
  * [Scraper](https://chrome.google.com/webstore/detail/scraper/mbigbapnjcgaffohmbkdlecaccepngjd)
  * [RethinkDB](https://www.rethinkdb.com/docs/install/)
  * [MongoDB](https://docs.mongodb.com/master/tutorial/install-mongodb-on-amazon/?_ga=1.85742745.1270707873.1490984659)
  * [PostgreSQL](https://www.postgresql.org/download/linux/)
  

#### Referências
  * [Scrapy 0.24 documentation [ENG]](https://doc.scrapy.org/en/0.24/)
  * [Guia de 10min com RethinkDB e Python [ENG]](https://www.rethinkdb.com/docs/guide/python/)
  * [MongoDB Documentation [ENG]](https://docs.mongodb.com/)
  * [Parte I - Configurando e rodando o Scrapy](http://www.gilenofilho.com.br/usando-o-scrapy-e-o-rethinkdb-para-capturar-e-armazenar-dados-imobiliarios-parte-i/)
  * [Parte II - Instalando, configurando e armazenando os dados no Rethinkdb](http://www.gilenofilho.com.br/usando-o-scrapy-e-o-rethinkdb-para-capturar-e-armazenar-dados-imobiliarios-parte-ii/)
  * [Parte III - Deploy do projeto Scrapy](http://www.gilenofilho.com.br/usando-o-scrapy-e-o-rethinkdb-para-capturar-e-armazenar-dados-imobiliarios-parte-iii/)
  * [XPath Tutorial [ENG]](https://www.w3schools.com/xml/xpath_intro.asp)
  * [Web Scraping with Python[ENG]](http://pdf.th7.cn/down/files/1603/Web%20Scraping%20with%20Python.pdf)
  * [Documentation PostgreSQL[ENG]](https://www.postgresql.org/docs/)
