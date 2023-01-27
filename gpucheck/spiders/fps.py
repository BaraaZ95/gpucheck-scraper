import scrapy
from urllib.parse import urljoin

class FpsSpider(scrapy.Spider):
    name = 'fps'
    allowed_domains = ['www.gpucheck.com']
    start_urls = ['https://www.gpucheck.com/graphics-cards']
    handle_httpstatus_list = [403]

    def parse(self, response):
        urls =  response.css('div[class="row"] > div[class = "hover"] > a::attr(href)').getall()
        urls = [urljoin(response.url, url) for url in urls]
        for url in urls:
            yield scrapy.Request(url,self.parse_gpu)
    
    async def parse_gpu(self, response):
        GPU = dict()
        table = response.css('div#summary > table')
        rows = table.css('tr')
        GPU['Name'] = ' '.join( rows[0].css('::text').getall()).strip()
        for row in rows:
            key = row.css('th::text').get()
            value = row.css('td::text').get()
            rating =  row.css('td> div::attr(title)').get()
            GPU.update({key: {'Value':value, 'Rating': rating}})
        GPU = {key.strip():value for key, value in GPU.items() if key}
        GPU['Overall Combination Score'] =  { 'Value':rows[21].xpath('./td[1]/text()').get(), 'Rating': rows[21].xpath('./td[2]/text()').get()}
        
        cpu = ''.join(GPU['Benchmark CPU']['Value'].split(r'(')[0]).replace('@','').strip()
        cpu = "-".join(cpu.split()).replace('.','-')
        settings = ['ultra','high', 'medium', 'low']
        GPU['Settings'] = {}
        for setting in settings:
            cpu_url = response.url + cpu + f'/{setting}#mainads'
            req =  scrapy.Request(cpu_url.lower(), callback= self.parse_fps)
            res =  await self.crawler.engine.download(req, self)         
            GPU['Settings'] .update( {setting: self.parse_fps(res)})
        
        GPU.pop('Description') #No need for this       
        yield GPU
    def parse_fps(self, response):
        resolution_fps = {}
        resolution_fps["Resolution"] = {}
        resolutions = ['res1920x1080', 'res2560x1440', 'res3440x1440', 'res3840x2160']
        for resolution in resolutions:
            resolution_fps["Resolution"].update({ resolution.replace('res',''): {"Games": []}})
            rows =  response.css(f'div[id="{resolution}"]> table>tbody>tr')
            for row in rows:
                release_date = row.css('td> span::text').get()
                game_name = row.css('td>a::text').get().strip()
                fps = row.css('td>div>div::text').getall()
                game_fps = {"Game_Name": game_name, "Release_Date": release_date, 'Min_FPS': fps[0], 'Avg_FPS': fps[1]}
                resolution_fps['Resolution'][ resolution.replace('res','')]['Games'].append(game_fps)
        return resolution_fps

                
    

            
        
             
            
        
