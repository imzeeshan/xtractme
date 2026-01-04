/**
 * Fix for Permissions Policy violation: unload event not allowed
 * 
 * This script replaces the deprecated 'unload' event listener in Django admin's
 * RelatedObjectLookups.js with modern alternatives (pagehide) that don't violate
 * browser Permissions Policy.
 * 
 * The script intercepts addEventListener calls to prevent 'unload' listeners
 * and converts them to 'pagehide' listeners instead.
 */
(function() {
    'use strict';

    // Override window.addEventListener IMMEDIATELY to intercept any future 'unload' listeners
    // This must run before any other scripts (like RelatedObjectLookups.js) try to add unload listeners
    const originalAddEventListener = window.addEventListener.bind(window);
    const originalRemoveEventListener = window.removeEventListener.bind(window);
    
    // Track unload listeners so we can manage them
    const unloadListeners = new WeakMap();
    
    window.addEventListener = function(type, listener, options) {
        if (type === 'unload' || type === 'beforeunload') {
            // Convert unload/beforeunload to pagehide
            // pagehide fires when the page is being unloaded and works with Permissions Policy
            const wrappedListener = function(event) {
                // Only call the original listener if the page is actually being unloaded
                // event.persisted is false when page is being unloaded (not just cached)
                if (!event.persisted && typeof listener === 'function') {
                    try {
                        // Create a synthetic event object that mimics unload event
                        const syntheticEvent = {
                            type: type,
                            target: window,
                            currentTarget: window,
                            bubbles: false,
                            cancelable: false,
                            defaultPrevented: false,
                            timeStamp: event.timeStamp,
                            originalEvent: event
                        };
                        listener.call(window, syntheticEvent);
                    } catch (e) {
                        // Silently handle errors
                        if (window.console && window.console.debug) {
                            window.console.debug('Error in converted unload listener:', e);
                        }
                    }
                }
            };
            
            // Store mapping for potential removal
            if (listener && typeof listener === 'function') {
                unloadListeners.set(listener, wrappedListener);
            }
            
            // Add as pagehide instead of unload
            return originalAddEventListener('pagehide', wrappedListener, options);
        }
        
        // For all other event types, use the original addEventListener
        return originalAddEventListener(type, listener, options);
    };
    
    // Also override removeEventListener to handle removal of converted listeners
    window.removeEventListener = function(type, listener, options) {
        if (type === 'unload' || type === 'beforeunload') {
            // Try to remove the converted listener
            const wrappedListener = unloadListeners.get(listener);
            if (wrappedListener) {
                unloadListeners.delete(listener);
                return originalRemoveEventListener('pagehide', wrappedListener, options);
            }
            return;
        }
        
        return originalRemoveEventListener(type, listener, options);
    };
})();
