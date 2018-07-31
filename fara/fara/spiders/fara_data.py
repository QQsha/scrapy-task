# -*- coding: utf-8 -*-
import re
import scrapy
import urllib.parse
from scrapy.http import FormRequest
from datetime import datetime




class FaraDataSpider(scrapy.Spider):
    name = 'fara_data'
    start_urls = ['https://efile.fara.gov/pls/apex/f?p=185:130:6392401800221::NO:RP,130:P130_DATERANGE:N']

    def __init__(self):
        self.page = 16
    
    
    def parse(self, response):
        next_button = response.xpath('//img[@title="Next"]').extract_first()
        for row in response.css('tr.even, tr.odd'):
            detail_url = row.css('tr > td > a::attr(href)').extract_first()
            full_link = response.urljoin(detail_url)
            country = urllib.parse.unquote(re.findall(r'Exhibit%20AB,(.*)$', detail_url)[0])
            date = row.xpath('td[contains(@headers, "FP_REG_DATE")]/text()').extract_first()
            item = {
                'url': full_link,
                'country': country,
                'state': row.xpath('td[contains(@headers, "STATE")]/text()').extract_first(),
                'reg_num': row.xpath('td[contains(@headers, "REG_NUMBER")]/text()').extract_first(),
                'address': row.xpath('td[contains(@headers, "ADDRESS_1")]/text()').extract_first().strip(),
                'foreign_principal': row.xpath('td[contains(@headers, "FP_NAME")]/text()').extract_first(),
                'date': datetime.strptime(date, "%m/%d/%Y").isoformat(),
                'registrant': row.xpath('td[contains(@headers, "REGISTRANT_NAME")]/text()').extract_first(),
            }
            yield scrapy.Request(
                item['url'],
                meta={'item': item},
                dont_filter=True,
                callback=self.parse_pdf
            )
        if next_button is not None:
            if 'params' not in response.meta:
                params = {
                    'p_request' : 'APXWGT',
                    'p_flow_id' : '185',
                    'p_flow_step_id' : '130',
                    'p_widget_num_return' : '15',
                    'p_widget_name' : 'worksheet',
                    'p_widget_mod' : 'ACTION',
                    'p_widget_action' : 'PAGE',
                    'x01': '555215554758934859',
                    'x02': '555216849652934863',
                    'p_instance' : response.xpath('//input[@id="pInstance"]/@value').extract_first(),
                }
            else:
                params = response.meta['params']
            

            next_page = "https://efile.fara.gov/pls/apex/wwv_flow.show"            
            p_widget_action_mod = 'pgR_min_row={}max_rows=15rows_fetched=15'.format(self.page)
            params['p_widget_action_mod'] = p_widget_action_mod
            self.page += 15
            request = scrapy.FormRequest(next_page, method="POST", formdata=params, callback=self.parse)
            request.meta['params'] = params
            yield request
            



    def parse_pdf(self, response):
        item = response.meta.get('item', {})
        recent_link = response.css('tr.even > td > a::attr(href)').extract_first()
        if recent_link is not None:
            item['exhibit_url'] = recent_link
            yield item

    

