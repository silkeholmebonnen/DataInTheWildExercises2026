# -*- coding: utf-8 -*-

"""
@author: lajello

A simple spider to login into LastFM

EXAMPLE OF FULL COMMAND:
scrapy crawl loginspider -o result.json -s LOG_FILE=LoginSpider.log

"""

import scrapy
from scrapy import FormRequest


class LoginSpider(scrapy.Spider):
    name = "loginspider"
    login_url = "https://secure.last.fm/login"

    async def start(self):
        # let's start by sending a first request to login page
        yield scrapy.Request(self.login_url, callback=self.parse_login)

    def parse_login(self, response):
        user_name = "YOUR_USERNAME_HERE"
        password = "YOUR_PASSWORD_HERE"

        hidden_field_1 = response.css("#login > input[type=hidden]:nth-child(1)")
        hidden_name_1 = hidden_field_1.css("::attr(name)").get()
        hidden_value_1 = hidden_field_1.css("::attr(value)").get()
        hidden_field_2 = response.css("#login > input[type=hidden]:nth-child(2)")
        hidden_name_2 = hidden_field_2.css("::attr(name)").get()
        hidden_value_2 = hidden_field_2.css("::attr(value)").get()

        # print(hidden_name_1, hidden_value_1, hidden_name_2, hidden_value_2)
        formdata = {"username_or_email": user_name, "password": password}
        return [
            FormRequest.from_response(
                response, formid="login", formdata=formdata, callback=self.start_crawl
            )
        ]

    def start_crawl(self, response):
        # check login succeed before going on
        print(response.status)
        # print(response.text)
        html_text = response.text

        if "YOUR_USERNAME_HERE" in html_text:
            print("Success")
            self.logger.info("Login successful")
            return
        elif "Please enter a correct username" in html_text:
            print("Failed")
            self.logger.error("Login failed")
        else:
            self.logger.error("?")
            print("uhmmm... something weird is happening...")

        # continue scraping with authenticated session...
