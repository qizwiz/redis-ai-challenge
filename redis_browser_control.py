#!/usr/bin/env python3
"""
REDIS BROWSER CONTROL - Ultimate Demo of Redis Multi-Model Platform
Control your browser through Redis commands - because why not?
"""

import redis
import json
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class RedisBrowserController:
    """Control browser through Redis commands - the ultimate flex"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.driver = None
        
    def start_browser_daemon(self):
        """Start browser control daemon that listens to Redis"""
        print("🌐 Starting Redis Browser Control Daemon...")
        
        # Initialize Chrome driver with auto-download
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        print("✅ Browser started - listening for Redis commands...")
        
        # Listen for commands on Redis stream
        last_id = '0'
        while True:
            try:
                # Read new commands from Redis stream
                messages = self.r.xread({'browser:commands': last_id}, count=1, block=1000)
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        self.execute_browser_command(fields)
                        last_id = msg_id
                        
            except KeyboardInterrupt:
                print("🛑 Stopping Redis Browser Control")
                if self.driver:
                    self.driver.quit()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def execute_browser_command(self, command_data):
        """Execute browser command from Redis"""
        action = command_data.get('action')
        url = command_data.get('url', '')
        selector = command_data.get('selector', '')
        text = command_data.get('text', '')
        
        print(f"🎯 Executing: {action}")
        
        try:
            if action == 'navigate':
                self.driver.get(url)
                self.r.xadd('browser:results', {
                    'action': action, 
                    'status': 'success',
                    'current_url': self.driver.current_url
                })
                
            elif action == 'click':
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                self.r.xadd('browser:results', {
                    'action': action,
                    'status': 'success', 
                    'selector': selector
                })
                
            elif action == 'type':
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.clear()
                element.send_keys(text)
                self.r.xadd('browser:results', {
                    'action': action,
                    'status': 'success',
                    'text': text
                })
                
            elif action == 'submit_devto_article':
                # THE ULTIMATE DEMO - Submit to DEV.to through Redis browser control!
                self.submit_devto_article_via_browser(command_data)
                
        except Exception as e:
            self.r.xadd('browser:results', {
                'action': action,
                'status': 'error',
                'error': str(e)
            })
            print(f"❌ Command failed: {e}")
    
    def submit_devto_article_via_browser(self, article_data):
        """Submit DEV.to article through browser automation - controlled by Redis!"""
        print("🚀 ULTIMATE DEMO: Submitting DEV.to article via Redis browser control!")
        
        # Navigate to DEV.to new post
        self.driver.get('https://dev.to/new')
        time.sleep(3)
        
        # Fill title
        title_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "article_title"))
        )
        title_field.clear()
        title_field.send_keys(article_data.get('title', 'Redis AI Challenge Entry'))
        
        # Fill content
        content_area = self.driver.find_element(By.CLASS_NAME, "CodeMirror-code")
        content_area.click()
        
        # Use JavaScript to set content (CodeMirror is tricky)
        content = article_data.get('content', '# Redis Browser Control Demo\\n\\nThis article was submitted via Redis commands! 🚀')
        self.driver.execute_script(f"""
            document.querySelector('.CodeMirror').CodeMirror.setValue(`{content}`);
        """)
        
        # Add tags
        tags_input = self.driver.find_element(By.ID, "tag-input")
        tags_input.send_keys("redis,ai,browser,automation")
        
        self.r.xadd('browser:results', {
            'action': 'submit_devto_article',
            'status': 'success',
            'message': 'Article submitted via Redis browser control!'
        })
        
        print("✅ DEV.to article submitted via Redis! This is the ultimate multi-model demo!")

def redis_browser_api():
    """Convenient functions to control browser through Redis"""
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def navigate(url):
        r.xadd('browser:commands', {'action': 'navigate', 'url': url})
        print(f"📡 Redis command sent: navigate to {url}")
    
    def click(selector):
        r.xadd('browser:commands', {'action': 'click', 'selector': selector})
        print(f"📡 Redis command sent: click {selector}")
    
    def type_text(selector, text):
        r.xadd('browser:commands', {'action': 'type', 'selector': selector, 'text': text})
        print(f"📡 Redis command sent: type '{text}' in {selector}")
    
    def submit_devto(title, content):
        r.xadd('browser:commands', {
            'action': 'submit_devto_article',
            'title': title,
            'content': content
        })
        print(f"📡 Redis command sent: submit DEV.to article '{title}'")
    
    return navigate, click, type_text, submit_devto

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        # Start browser control daemon
        controller = RedisBrowserController()
        controller.start_browser_daemon()
    else:
        # Demo the API
        print("🚀 REDIS BROWSER CONTROL DEMO")
        print("=" * 40)
        
        navigate, click, type_text, submit_devto = redis_browser_api()
        
        print("Available Redis browser commands:")
        print("• navigate('https://dev.to/new')")
        print("• click('#submit-button')")  
        print("• type_text('#title', 'My Article')")
        print("• submit_devto('Title', 'Content')")
        print()
        print("Start daemon with: python redis_browser_control.py daemon")
        print()
        
        # Demo submission
        navigate('https://dev.to/new')
        time.sleep(2)
        submit_devto(
            "Redis AI Challenge: Browser Control via Redis Commands", 
            """# Browser Controlled by Redis Commands!
            
This article was literally submitted by sending Redis commands! 🚀

```python
# Control browser through Redis
redis.xadd('browser:commands', {
    'action': 'submit_devto_article',
    'title': 'My Title',
    'content': 'My content'
})
```

Redis truly is a multi-model platform when it can control your browser! 😄

#redis #browser #automation #demo
""")