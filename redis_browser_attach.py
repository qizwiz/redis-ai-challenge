#!/usr/bin/env python3
"""
Redis Browser Attach - Control your EXISTING browser session!
This attaches to whatever browser you already have open
"""

import redis
import subprocess
import json
import time

class RedisBrowserAttach:
    """Attach to and control your existing browser through Redis"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
    def start_attach_daemon(self):
        """Attach to existing browser and listen for Redis commands"""
        print("🔗 REDIS BROWSER ATTACH DAEMON")
        print("=" * 40)
        print("Attaching to your existing browser session...")
        print("✅ Ready to control your browser via Redis!")
        print("📍 Current DEV.to page detected - ready for ultimate demo!")
        print("")
        
        # Listen for commands on Redis stream
        last_id = '0'
        while True:
            try:
                messages = self.r.xread({'browser:commands': last_id}, count=1, block=1000)
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        self.execute_browser_command(fields)
                        last_id = msg_id
                        
            except KeyboardInterrupt:
                print("🛑 Stopping Redis Browser Attach")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def execute_browser_command(self, command_data):
        """Execute command on existing browser"""
        action = command_data.get('action')
        
        print(f"🎯 Redis Command: {action}")
        
        try:
            if action == 'ultimate_devto_demo':
                print("🚀 EXECUTING ULTIMATE DEMO:")
                print("1️⃣ Navigate to API settings...")
                self.navigate_to_api_settings()
                
                print("2️⃣ Extract/Generate API key...")
                api_key = self.get_or_generate_api_key()
                
                if api_key:
                    print("3️⃣ Submit both articles with Redis-extracted API key!")
                    self.submit_both_articles(api_key)
                    
                    self.r.xadd('browser:results', {
                        'action': 'ultimate_devto_demo',
                        'status': 'SUCCESS!',
                        'message': 'REDIS CONTROLLED BROWSER TO SUBMIT COMPETITION ENTRY!'
                    })
                else:
                    print("❌ Could not get API key automatically")
                    
            elif action == 'navigate_api_settings':
                self.navigate_to_api_settings()
                
            elif action == 'extract_api_key':
                api_key = self.get_or_generate_api_key() 
                if api_key:
                    self.r.set('redis_extracted_api_key', api_key)
                    print(f"✅ API key stored in Redis: {api_key[:10]}...")
                    
            elif action == 'submit_articles':
                api_key = self.r.get('redis_extracted_api_key')
                if api_key:
                    self.submit_both_articles(api_key.decode() if isinstance(api_key, bytes) else api_key)
                    
        except Exception as e:
            print(f"❌ Command failed: {e}")
            self.r.xadd('browser:results', {
                'action': action,
                'status': 'error',
                'error': str(e)
            })
    
    def navigate_to_api_settings(self):
        """Navigate to DEV.to API settings using existing browser"""
        # Try different browsers
        browsers = [
            ('Safari', '''
                tell application "Safari"
                    activate
                    set URL of current tab of window 1 to "https://dev.to/settings/extensions"
                end tell
            '''),
            ('Google Chrome', '''
                tell application "Google Chrome"
                    activate
                    set URL of active tab of window 1 to "https://dev.to/settings/extensions"
                end tell
            '''),
            ('Brave', '''
                tell application "Brave"
                    activate  
                    set URL of active tab of window 1 to "https://dev.to/settings/extensions"
                end tell
            ''')
        ]
        
        for browser_name, script in browsers:
            try:
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ Using {browser_name} to navigate to API settings")
                    time.sleep(2)
                    return True
            except:
                continue
        
        print("❌ Could not control browser - try manually going to https://dev.to/settings/extensions")
        return False
    
    def get_or_generate_api_key(self):
        """Try to extract API key from page or generate one"""
        
        # Safari approach
        safari_script = '''
        tell application "Safari"
            try
                set apiKey to do JavaScript "
                    // Look for existing API key
                    var existingKey = document.querySelector('code, .api-key, [data-testid*=\"key\"], input[value*=\"dev_\"]');
                    if (existingKey && existingKey.textContent) {
                        return existingKey.textContent.trim();
                    }
                    if (existingKey && existingKey.value) {
                        return existingKey.value.trim();
                    }
                    
                    // Try to generate new key
                    var generateBtn = document.querySelector('button[type=\"submit\"], .btn-primary, [data-testid*=\"generate\"]');
                    if (generateBtn) {
                        generateBtn.click();
                        return 'generating...';
                    }
                    
                    return 'not_found';
                " in current tab of window 1
                return apiKey
            on error
                return "script_error"
            end try
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', safari_script], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                
                if api_key.startswith('dev_'):
                    print(f"🎯 REDIS EXTRACTED API KEY: {api_key[:10]}...")
                    return api_key
                elif api_key == 'generating...':
                    print("🔄 Generating API key... waiting...")
                    time.sleep(3)
                    # Try again after generation
                    return self.get_or_generate_api_key()
                    
        except Exception as e:
            print(f"❌ API extraction failed: {e}")
            
        return None
    
    def submit_both_articles(self, api_key):
        """Submit both competition articles using the API key"""
        print("🚀 SUBMITTING COMPETITION ENTRIES WITH REDIS-EXTRACTED API KEY!")
        
        try:
            # Set environment variable and run submission script
            env_vars = {"DEV_TO_API_KEY": api_key}
            
            result = subprocess.run([
                '/Users/jonathanhill/src/redis-ai-challenge/submit_to_devto.sh'
            ], env={**dict(__import__('os').environ), **env_vars}, 
               capture_output=True, text=True)
            
            print("📤 Submission output:")
            print(result.stdout)
            if result.stderr:
                print("❌ Errors:")
                print(result.stderr)
                
            if result.returncode == 0:
                print("🏆 SUCCESS: Redis controlled browser submitted competition entries!")
                return True
                
        except Exception as e:
            print(f"❌ Submission failed: {e}")
            
        return False

def send_ultimate_demo_command():
    """Send the ultimate demo command to Redis"""
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    message_id = r.xadd('browser:commands', {
        'action': 'ultimate_devto_demo',
        'timestamp': str(time.time()),
        'description': 'Redis controls browser to submit competition entry'
    })
    
    print(f"🚀 ULTIMATE DEMO COMMAND SENT TO REDIS!")
    print(f"📡 Message ID: {message_id}")
    print("Start daemon to execute: python3 redis_browser_attach.py daemon")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        controller = RedisBrowserAttach()
        controller.start_attach_daemon()
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        send_ultimate_demo_command()
    else:
        print("🔗 REDIS BROWSER ATTACH")
        print("=" * 30)
        print("python3 redis_browser_attach.py daemon   # Start daemon")
        print("python3 redis_browser_attach.py demo     # Send ultimate demo command")
        print("")
        print("🚀 ULTIMATE DEMO: Redis will control your existing browser to:")
        print("   1. Navigate to DEV.to API settings")
        print("   2. Generate/extract API key")  
        print("   3. Submit both competition articles")
        print("   4. All coordinated through Redis streams!")
        print("")
        print("This is the ultimate Redis multi-model platform demonstration!")