#!/usr/bin/env python3
import subprocess
import json
import time
import redis

class HIDController:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.device_registry = {}
        
    def enumerate_devices(self):
        """Find all connected HID devices"""
        try:
            # Use system_profiler to find USB devices
            result = subprocess.run([
                'system_profiler', 'SPUSBDataType', '-json'
            ], capture_output=True, text=True, check=True)
            
            usb_data = json.loads(result.stdout)
            devices = []
            
            for item in usb_data.get('SPUSBDataType', []):
                if self._is_hid_device(item):
                    devices.append({
                        'name': item.get('_name', 'Unknown'),
                        'product_id': item.get('product_id', ''),
                        'vendor_id': item.get('vendor_id', ''),
                        'type': self._detect_device_type(item.get('_name', ''))
                    })
            
            self.device_registry = {i: dev for i, dev in enumerate(devices)}
            self.redis_client.hset('hid:devices', mapping=self.device_registry)
            
            print(f"Found {len(devices)} HID devices")
            return devices
            
        except Exception as e:
            print(f"Device enumeration error: {e}")
            return []
    
    def _is_hid_device(self, item):
        """Check if USB item is HID device"""
        name = item.get('_name', '').lower()
        return any(keyword in name for keyword in ['mouse', 'keyboard', 'trackpad', 'touchpad'])
    
    def _detect_device_type(self, name):
        """Detect device type from name"""
        name_lower = name.lower()
        if 'mouse' in name_lower:
            return 'mouse'
        elif 'keyboard' in name_lower:
            return 'keyboard'
        elif any(word in name_lower for word in ['trackpad', 'touchpad']):
            return 'trackpad'
        return 'unknown'
    
    def create_virtual_device(self, device_type):
        """Create virtual HID device for AI control"""
        virtual_device = {
            'id': f'virtual_{device_type}_{int(time.time())}',
            'type': device_type,
            'status': 'active',
            'created': int(time.time())
        }
        
        self.redis_client.hset(f'hid:virtual:{virtual_device["id"]}', mapping=virtual_device)
        print(f"Created virtual {device_type} device: {virtual_device['id']}")
        
        return virtual_device
    
    def route_input(self, device_id, target_process):
        """Route input from device to specific process"""
        routing_config = {
            'device_id': device_id,
            'target_process': target_process,
            'timestamp': int(time.time()),
            'status': 'active'
        }
        
        self.redis_client.hset(f'hid:routing:{device_id}', mapping=routing_config)
        print(f"Routed device {device_id} to process {target_process}")
        
        return routing_config

if __name__ == "__main__":
    controller = HIDController()
    
    # Enumerate existing devices
    devices = controller.enumerate_devices()
    print(f"Enumerated devices: {devices}")
    
    # Create virtual devices for AI control
    virtual_mouse = controller.create_virtual_device('mouse')
    virtual_keyboard = controller.create_virtual_device('keyboard')
    
    print("HID Controller initialized and ready")
