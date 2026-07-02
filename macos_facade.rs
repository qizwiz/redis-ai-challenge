// macOS Native Facade - WASM Module
// Replaces neurocommander.sh with native speed and reliability

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_void};
use std::slice;

// C FFI declarations for macOS frameworks
#[link(name = "CoreGraphics", kind = "framework")]
extern "C" {
    fn CGMainDisplayID() -> u32;
    fn CGDisplayBounds(display: u32) -> CGRect;
    fn CGEventCreateMouseEvent(
        source: *mut c_void,
        mouse_type: u32,
        mouse_pos: CGPoint,
        button: u32,
    ) -> *mut c_void;
    fn CGEventPost(tap: u32, event: *mut c_void);
}

#[repr(C)]
struct CGPoint {
    x: f64,
    y: f64,
}

#[repr(C)]
struct CGRect {
    origin: CGPoint,
    size: CGSize,
}

#[repr(C)]
struct CGSize {
    width: f64,
    height: f64,
}

// State vector matching your Python matrix_system.py
#[repr(C)]
pub struct StateVector {
    timestamp: f64,
    windows_count: u32,
    processes_count: u32,
    files_count: u32,
    mouse_x: f64,
    mouse_y: f64,
    display_width: f64,
    display_height: f64,
}

// WASM exports - callable from Python/JS
#[no_mangle]
pub extern "C" fn capture_state() -> StateVector {
    let display_id = unsafe { CGMainDisplayID() };
    let bounds = unsafe { CGDisplayBounds(display_id) };

    StateVector {
        timestamp: get_timestamp(),
        windows_count: count_windows(),
        processes_count: count_processes(),
        files_count: 0, // Will add FSEvents
        mouse_x: get_mouse_x(),
        mouse_y: get_mouse_y(),
        display_width: bounds.size.width,
        display_height: bounds.size.height,
    }
}

#[no_mangle]
pub extern "C" fn click_at(x: f64, y: f64) {
    unsafe {
        let event = CGEventCreateMouseEvent(
            std::ptr::null_mut(),
            1, // kCGEventLeftMouseDown
            CGPoint { x, y },
            0,
        );
        CGEventPost(0, event);

        let event = CGEventCreateMouseEvent(
            std::ptr::null_mut(),
            2, // kCGEventLeftMouseUp
            CGPoint { x, y },
            0,
        );
        CGEventPost(0, event);
    }
}

#[no_mangle]
pub extern "C" fn get_display_info() -> *const u8 {
    let display_id = unsafe { CGMainDisplayID() };
    let bounds = unsafe { CGDisplayBounds(display_id) };

    let info = format!(
        "{{\"width\":{},\"height\":{}}}",
        bounds.size.width as i32,
        bounds.size.height as i32
    );

    let c_str = CString::new(info).unwrap();
    c_str.into_raw() as *const u8
}

// Helper functions
fn get_timestamp() -> f64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
}

fn count_windows() -> u32 {
    // Simplified - will use Accessibility API
    // Currently returns stub
    0
}

fn count_processes() -> u32 {
    // Will use sysctl - much faster than ps aux
    // Currently returns stub
    100
}

fn get_mouse_x() -> f64 {
    // Will use CGEventGetLocation
    0.0
}

fn get_mouse_y() -> f64 {
    0.0
}

// Memory management for strings returned to host
#[no_mangle]
pub extern "C" fn free_string(ptr: *mut c_char) {
    unsafe {
        if !ptr.is_null() {
            let _ = CString::from_raw(ptr);
        }
    }
}
