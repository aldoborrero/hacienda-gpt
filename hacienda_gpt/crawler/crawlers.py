from collections.abc import Generator
import hashlib
import os
import re
from typing import Any
from urllib.parse import urlparse

from pathvalidate import sanitize_filepath
import scrapy
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod


class AgenciaTributariaWebCrawler(scrapy.Spider):
    name = "AgenciaTributariaWebCrawler"
    urls = [
        "https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/irpf-2022/numero-identificacion-publicacion.html"
    ]
    allowed_paths = [r"/Sede/ayuda/manuales-videos-folletos/manuales-practicos/irpf-2022/"]

    def __init__(self, folder: str = None, mode: str = "flat", *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.folder: str = folder
        self.mode: str = mode
        self.allowed_patterns: list[re.Pattern] = [re.compile(path) for path in self.allowed_paths]
        self._ensure_folder_exists()

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        for url in self.urls:
            yield scrapy.Request(url, meta=self._get_meta_for_request(url), callback=self.parse)

    def parse(self, response: Response) -> Generator[scrapy.Request, None, None]:
        self._save_response_to_file(response)
        yield from self._follow_domain_links(response)

    def _get_meta_for_request(self, url: str) -> dict[str, Any]:
        return {"playwright": True, "playwright_page_methods": self._get_page_methods(url)}

    def _get_page_methods(self, url: str) -> list[PageMethod]:
        return [
            PageMethod("wait_for_selector", "div#indice-modal nav"),
            PageMethod(
                "wait_for_function",
                expression="() => Array.from($('div#indice-modal nav a')).filter(el => el.href === '#').length === 0",
            ),
            PageMethod("screenshot", path=self._generate_screenshot_path(url), full_page=True),
        ]

    def _ensure_folder_exists(self) -> None:
        os.makedirs(self.folder, exist_ok=True)

    def _save_response_to_file(self, response: Response) -> None:
        with open(self._generate_file_path(response), "wb") as f:
            f.write(response.body)

    def _follow_domain_links(self, response: Response) -> Generator[scrapy.Request, None, None]:
        link_extractor = LinkExtractor(allow=self.allowed_patterns)
        links = link_extractor.extract_links(response)
        for link in links:
            yield scrapy.Request(url=link.url, meta=self._get_meta_for_request(link.url), callback=self.parse)

    def _generate_screenshot_path(self, url: str) -> str:
        return os.path.join(self.folder, f"{hashlib.md5(url.encode()).hexdigest()}.png")

    def _generate_file_path(self, response: Response) -> str:
        return (
            os.path.join(self.folder, f"{hashlib.md5(response.url.encode()).hexdigest()}.html")
            if self.mode == "flat"
            else self._generate_structure_file_path(response)
        )

    def _generate_structure_file_path(self, response: Response) -> str:
        parsed_url = urlparse(response.url)
        full_path = os.path.join(self.folder, sanitize_filepath(parsed_url.path[1:]))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path


class AgenciaTributariaPDFCrawler(scrapy.Spider):
    name = "AgenciaTributariaPDFCrawler"
    start_urls = ["https://agenciatributaria.gob.es/"]

    def __init__(self, folder=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = folder

    def parse(self, response):
        le = LinkExtractor()
        for link in le.extract_links(response):
            yield {"file_urls": [link.url], "path": self.folder}
        self._follow_domain_links(response)

    def _follow_domain_links(self, response):
        domain = self._extract_domain_from_start_url()
        link_extractor = LinkExtractor(allow_domains=[domain])
        for link in link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)
