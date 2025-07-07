import axios from 'axios'

// Check if we're in debug mode
const isDebugMode = import.meta.env.VITE_DEBUG === 'true' || import.meta.env.VITE_API_LOG_LEVEL === 'debug'

// Create axios instance with base configuration
const api = axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor for logging
api.interceptors.request.use(
    (config) => {
        if (isDebugMode) {
            console.group(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
            console.log('Headers:', config.headers)
            if (config.data) {
                console.log('Request Data:', config.data)
                // Also log as string for exact payload inspection
                console.log('Request JSON:', JSON.stringify(config.data))
            }
            console.log('Full config:', config)
            console.groupEnd()
        } else {
            console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
        }
        return config
    },
    (error) => {
        console.error('❌ Request error:', error)
        return Promise.reject(error)
    }
)

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => {
        if (isDebugMode) {
            console.group(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`)
            console.log('Response Data:', response.data)
            console.log('Response Headers:', response.headers)
            console.groupEnd()
        }
        return response
    },
    (error) => {
        if (isDebugMode) {
            console.group('❌ API Error:')
            console.error('Original Request:', error.config?.method?.toUpperCase(), error.config?.url)
            console.error('Error Message:', error.message)

            if (error.response) {
                console.error('Status:', error.response.status, error.response.statusText)
                console.error('Headers:', error.response.headers)
                console.error('Data:', error.response.data)
            }

            if (error.request) {
                console.error('Request was made but no response received')
                console.error('Request Details:', error.request)
            }

            console.error('Full Error:', error)
            console.groupEnd()
        } else {
            console.error('API Error:', error.response?.data || error.message)
        }
        return Promise.reject(error)
    }
)

export const apiClient = {
    // Health check
    async healthCheck() {
        if (isDebugMode) console.log('API: Health check')
        const response = await api.get('/health')
        return response.data
    },

    // CIDR operations
    async listCidrs() {
        if (isDebugMode) console.log('API: Listing CIDR blocks')
        const response = await api.get('/cidrs')
        return response.data
    },

    async getCidr(cidrId) {
        if (isDebugMode) console.log(`API: Getting CIDR block: ${cidrId}`)
        const response = await api.get(`/cidrs/${encodeURIComponent(cidrId)}`)
        return response.data
    },

    async createCidr(cidrData) {
        if (isDebugMode) {
            console.group('API: Creating new CIDR block')
            console.log('CIDR Data:', cidrData)
            console.log('Parent:', cidrData.parent || 'none')
            console.log('Using POST to /cidrs')
            console.groupEnd()
        }
        const response = await api.post('/cidrs', cidrData)
        return response.data
    },

    async updateCidr(cidrId, cidrData) {
        if (isDebugMode) {
            console.group('API: Updating CIDR block')
            console.log('CIDR ID:', cidrId)
            console.log('CIDR Data:', cidrData)
            console.log(`Using PUT to /cidrs/${encodeURIComponent(cidrId)}`)
            console.groupEnd()
        }
        const response = await api.put(`/cidrs/${encodeURIComponent(cidrId)}`, cidrData)
        return response.data
    },

    async deleteCidr(cidrId) {
        const response = await api.delete(`/cidrs/${encodeURIComponent(cidrId)}`)
        return response.data
    }
}

export default api
