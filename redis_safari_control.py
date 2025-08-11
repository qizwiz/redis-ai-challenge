#!/usr/bin/env python3
"""
Redis Safari Control - Ultimate Demo using AppleScript
Control Safari through Redis commands on macOS
"""

import redis
import subprocess
import json
import time

class RedisSafariController:
    """Control Safari through Redis commands using AppleScript"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
    def start_safari_daemon(self):
        """Start Safari control daemon that listens to Redis"""
        print("🦁 Starting Redis Safari Control Daemon...")
        print("✅ Safari ready - listening for Redis commands...")
        
        # Listen for commands on Redis stream
        last_id = '0'
        while True:
            try:
                # Read new commands from Redis stream
                messages = self.r.xread({'browser:commands': last_id}, count=1, block=1000)
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        self.execute_safari_command(fields)
                        last_id = msg_id
                        
            except KeyboardInterrupt:
                print("🛑 Stopping Redis Safari Control")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def execute_safari_command(self, command_data):
        """Execute Safari command using AppleScript"""
        action = command_data.get('action')
        url = command_data.get('url', '')
        selector = command_data.get('selector', '')
        text = command_data.get('text', '')
        
        print(f"🎯 Executing Safari command: {action}")
        
        try:
            if action == 'navigate':
                script = f'''
                tell application "Safari"
                    activate
                    set URL of current tab of window 1 to "{url}"
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                
                self.r.xadd('browser:results', {
                    'action': action,
                    'status': 'success',
                    'url': url
                })
                
            elif action == 'get_api_key':
                # The ultimate demo - extract API key from DEV.to settings page
                script = '''
                tell application "Safari"
                    activate
                    set URL of current tab of window 1 to "https://dev.to/settings/extensions"
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                time.sleep(3)
                
                # Check if API key is visible and extract it
                extract_script = '''
                tell application "Safari"
                    set pageContent to do JavaScript "document.body.innerText" in current tab of window 1
                    return pageContent
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', extract_script], 
                                      capture_output=True, text=True)
                
                if "API Key" in result.stdout:
                    # Try to extract API key pattern
                    api_key_script = '''
                    tell application "Safari"
                        set apiKey to do JavaScript "
                            var apiElement = document.querySelector('input[type=\"text\"][value*=\"dev_\"]');
                            if (apiElement) { 
                                return apiElement.value; 
                            } else {
                                var generateBtn = document.querySelector('button, input[type=\"submit\"]');
                                if (generateBtn) generateBtn.click();
                                return 'generating...';
                            }
                        " in current tab of window 1
                        return apiKey
                    end tell
                    '''
                    
                    api_result = subprocess.run(['osascript', '-e', api_key_script], 
                                              capture_output=True, text=True)
                    
                    if api_result.stdout.strip().startswith('dev_'):
                        api_key = api_result.stdout.strip()
                        # Store API key in Redis!
                        self.r.set('devto_api_key', api_key)
                        
                        self.r.xadd('browser:results', {
                            'action': 'get_api_key',
                            'status': 'success',
                            'api_key': api_key[:10] + '...',  # Partial key for security
                            'message': 'API key extracted and stored in Redis!'
                        })
                        
                        return api_key
                
                self.r.xadd('browser:results', {
                    'action': 'get_api_key', 
                    'status': 'info',
                    'message': 'Please generate API key manually at https://dev.to/settings/extensions'
                })
                
            elif action == 'submit_with_redis_api_key':
                # Use the API key stored in Redis to submit articles!
                api_key = self.r.get('devto_api_key')
                if api_key:
                    self.submit_articles_with_api_key(api_key)
                else:
                    print("❌ No API key found in Redis")
                
        except Exception as e:
            self.r.xadd('browser:results', {
                'action': action,
                'status': 'error',
                'error': str(e)
            })
            print(f"❌ Command failed: {e}")
    
    def submit_articles_with_api_key(self, api_key):
        """Submit both DEV.to articles using API key from Redis"""
        print("🚀 ULTIMATE DEMO: Submitting articles with API key extracted from browser!")
        
        # Submit both articles using the API key that Redis extracted from browser
        subprocess.run([
            '/bin/bash', '-c', 
            f'DEV_TO_API_KEY="{api_key}" /Users/jonathanhill/src/redis-ai-challenge/submit_to_devto.sh'
        ])
        
        self.r.xadd('browser:results', {
            'action': 'ultimate_submission',
            'status': 'success', 
            'message': 'Articles submitted using API key extracted by Redis from browser!'
        })

if __name__ == "__main__":
    controller = RedisSafariController()
    
    if len(__import__('sys').argv) > 1 and __import__('sys').argv[1] == "daemon":
        controller.start_safari_daemon()
    else:
        print("🦁 Redis Safari Control Ready")
        print("Start with: python3 redis_safari_control.py daemon")
        print("")
        print("🚀 ULTIMATE DEMO COMMANDS:")
        print("redis-cli XADD browser:commands * action get_api_key")
        print("redis-cli XADD browser:commands * action submit_with_redis_api_key")