# # -*- coding: utf-8 -*-
import scrapy

from scrapy.spiders import BaseSpider
from scrapy.selector import HtmlXPathSelector
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