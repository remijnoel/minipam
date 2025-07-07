/**
 * Debug utilities for MiniPAM web UI
 * 
 * This module provides debugging tools and utilities for the MiniPAM web UI.
 * It's enabled when VITE_DEBUG is set to 'true'.
 */

// Check if debug mode is enabled
const isDebugMode = import.meta.env.VITE_DEBUG === 'true' || import.meta.env.VITE_API_LOG_LEVEL === 'debug'

/**
 * Log a debug message if debug mode is enabled
 * 
 * @param {string} message - The message to log
 * @param {any} data - Optional data to log
 */
function logDebug(message, data) {
    if (!isDebugMode) return

    if (data) {
        console.group(`🐞 ${message}`)
        console.log(data)
        console.groupEnd()
    } else {
        console.log(`🐞 ${message}`)
    }
}

/**
 * Log component lifecycle events
 * 
 * @param {string} component - Component name
 * @param {string} event - Lifecycle event name
 * @param {Object} props - Component props
 */
function logComponentEvent(component, event, props) {
    if (!isDebugMode) return

    console.group(`🔄 ${component}: ${event}`)
    if (props) {
        console.log('Props:', props)
    }
    console.groupEnd()
}

/**
 * Log UI events like button clicks, form submissions, etc.
 * 
 * @param {string} component - Component name
 * @param {string} event - Event name
 * @param {any} data - Event data
 */
function logUIEvent(component, event, data) {
    if (!isDebugMode) return

    console.group(`👆 UI Event: ${component} - ${event}`)
    if (data) {
        console.log('Data:', data)
    }
    console.groupEnd()
}

/**
 * Log state changes
 * 
 * @param {string} component - Component name
 * @param {string} property - Property name
 * @param {any} oldValue - Old value
 * @param {any} newValue - New value
 */
function logStateChange(component, property, oldValue, newValue) {
    if (!isDebugMode) return

    console.group(`🔄 State Change: ${component} - ${property}`)
    console.log('Old:', oldValue)
    console.log('New:', newValue)
    console.groupEnd()
}

export default {
    isDebugMode,
    logDebug,
    logComponentEvent,
    logUIEvent,
    logStateChange
}
