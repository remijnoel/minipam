<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900">MiniPAM</h1>
            <span class="ml-2 text-sm text-gray-500">CIDR Management</span>
          </div>
          
          <!-- Health Status -->
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  healthStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                ]"
              ></div>
              <span class="text-sm text-gray-600">
                {{ healthStatus === 'healthy' ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
            
            <button
              @click="refreshData"
              :disabled="isLoading"
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              <svg 
                :class="['w-4 h-4 mr-2', isLoading ? 'animate-spin' : '']" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <!-- Error Message -->
      <div v-if="error" class="mb-6">
        <div class="bg-red-50 border border-red-200 rounded-md p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                <span v-if="error.includes('CIDR block') || error.includes('should be assigned')">Validation Error</span>
                <span v-else>Error</span>
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>{{ error }}</p>
                <p v-if="error.includes('should be assigned')" class="mt-2 italic">
                  This is due to the "smallest parent" rule: CIDR blocks must be assigned to their most specific parent.
                </p>
              </div>
            </div>
            <div class="ml-auto pl-3">
              <button @click="error = null" class="text-red-400 hover:text-red-600">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Debug Mode Indicator (only visible in debug mode) -->
      <div v-if="debugMode" class="mb-6">
        <div class="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div class="ml-3 flex justify-between w-full">
              <div>
                <h3 class="text-sm font-medium text-yellow-800">Debug Mode Active</h3>
                <div class="mt-1 text-xs text-yellow-700">
                  Open browser console to see detailed logs
                </div>
              </div>
              <button @click="showDebugInfo" class="text-sm text-blue-500 hover:text-blue-700">
                Show Details
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- CIDR Management Interface -->
      <div class="space-y-6">
        <!-- Create New CIDR Button -->
        <div class="flex justify-between items-center">
          <h2 class="text-lg font-medium text-gray-900">CIDR Blocks</h2>
          <button
            @click="showCreateForm = true"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add CIDR Block
          </button>
        </div>

        <!-- CIDR Table -->
        <CidrTable 
          :cidrs="cidrs"
          :loading="isLoading"
          @edit="handleEdit"
          @delete="handleDelete"
          @view="handleView"
          @createChild="handleCreateChild"
        />

        <!-- Create/Edit Form Modal -->
        <CidrForm
          v-if="showCreateForm || editingCidr"
          :cidr="editingCidr"
          :show="showCreateForm || !!editingCidr"
          :error="formError"
          @save="handleSave"
          @cancel="handleCancel"
        />

        <!-- View Details Modal -->
        <CidrDetails
          v-if="viewingCidr"
          :cidr="viewingCidr"
          :show="!!viewingCidr"
          @close="viewingCidr = null"
          @edit="handleEdit"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { apiClient } from './api/client.js'
import CidrTable from './components/CidrTable.vue'
import CidrForm from './components/CidrForm.vue'
import CidrDetails from './components/CidrDetails.vue'
import debugUtils from './utils/debug.js'

// Debug mode detection
const debugMode = ref(debugUtils.isDebugMode)

// Reactive state
const cidrs = ref([])
const isLoading = ref(false)
const error = ref(null)
const formError = ref(null)
const healthStatus = ref('unknown')
const showCreateForm = ref(false)
const editingCidr = ref(null)
const viewingCidr = ref(null)

// Watch for state changes in debug mode
if (debugMode.value) {
  watch(cidrs, (newValue, oldValue) => {
    debugUtils.logStateChange('App', 'cidrs', oldValue, newValue)
  })
  
  watch(healthStatus, (newValue, oldValue) => {
    debugUtils.logStateChange('App', 'healthStatus', oldValue, newValue)
  })
  
  debugUtils.logDebug('App component initialized')
}

// Load initial data
onMounted(() => {
  debugUtils.logComponentEvent('App', 'onMounted')
  loadData()
})

async function loadData() {
  debugUtils.logDebug('Loading data')
  await Promise.all([
    checkHealth(),
    loadCidrs()
  ])
}

async function checkHealth() {
  try {
    const health = await apiClient.healthCheck()
    healthStatus.value = health.status
    debugUtils.logDebug('Health check result', health)
  } catch (err) {
    healthStatus.value = 'error'
    debugUtils.logDebug('Health check failed', err)
  }
}

async function loadCidrs() {
  isLoading.value = true
  error.value = null
  
  try {
    cidrs.value = await apiClient.listCidrs()
    debugUtils.logDebug(`Loaded ${cidrs.value.length} CIDR blocks`)
  } catch (err) {
    error.value = err.userMessage || `Failed to load CIDR blocks: ${err.message}`
    debugUtils.logDebug('Failed to load CIDR blocks', err)
  } finally {
    isLoading.value = false
  }
}

async function refreshData() {
  debugUtils.logUIEvent('App', 'refresh')
  await loadData()
}

function handleEdit(cidr) {
  debugUtils.logUIEvent('App', 'edit', cidr)
  editingCidr.value = { ...cidr }
  showCreateForm.value = false
}

function handleView(cidr) {
  debugUtils.logUIEvent('App', 'view', cidr)
  viewingCidr.value = cidr
}

function handleCreateChild(parentCidr) {
  debugUtils.logUIEvent('App', 'createChild', parentCidr)
  // Create a new CIDR with the parent field pre-populated
  // Important: We're NOT setting a CIDR value here, which means we're in CREATE mode
  // not EDIT mode. This is essential for the handleSave function to work correctly.
  editingCidr.value = {
    cidr: '', // Empty CIDR = create new one
    name: '',
    description: '',
    tags: {},
    parent: parentCidr.cidr // Pre-populate parent field
  }
  showCreateForm.value = true
}

async function handleDelete(cidr) {
  debugUtils.logUIEvent('App', 'delete', cidr)
  
  if (!confirm(`Are you sure you want to delete CIDR block ${cidr.cidr}?`)) {
    return
  }

  try {
    await apiClient.deleteCidr(cidr.cidr)
    await loadCidrs()
  } catch (err) {
    // Use the enhanced error message from the API client if available
    error.value = err.userMessage || `Failed to delete CIDR block: ${err.message}`
    debugUtils.logDebug('Delete operation failed', err)
  }
}

async function handleSave(cidrData) {
  debugUtils.logUIEvent('App', 'save', cidrData)
  
  // Clear any previous form errors
  formError.value = null
  
  try {
    // The key issue: when we're in edit mode with a pre-existing CIDR, update it
    // Otherwise, always create a new CIDR (even when creating a child)
    if (editingCidr.value && editingCidr.value.cidr) {
      // Update existing CIDR - must have a valid CIDR ID
      debugUtils.logDebug('Updating existing CIDR', { id: editingCidr.value.cidr, data: cidrData })
      await apiClient.updateCidr(editingCidr.value.cidr, cidrData)
    } else {
      // Create new CIDR (including child CIDRs)
      debugUtils.logDebug('Creating new CIDR', cidrData)
      await apiClient.createCidr(cidrData)
    }
    
    await loadCidrs()
    handleCancel()
  } catch (err) {
    // Use the enhanced error message from the API client if available
    const errorMessage = err.userMessage || `Failed to save CIDR block: ${err.message}`
    
    // If it's a validation error (422), show it in the form
    if (err.response && err.response.status === 422) {
      formError.value = errorMessage
    } else {
      // For other errors, show in the main error area
      error.value = errorMessage
    }
    
    // In debug mode, show more detailed error information
    if (debugMode.value) {
      if (err.response?.data?.detail) {
        console.log('Detailed error info:', err.response.data.detail)
      }
    }
    
    debugUtils.logDebug('Save operation failed', err)
  }
}

function handleCancel() {
  debugUtils.logUIEvent('App', 'cancel')
  showCreateForm.value = false
  editingCidr.value = null
  formError.value = null
}

function showDebugInfo() {
  debugUtils.logUIEvent('App', 'showDebugInfo')
  console.group('🐞 MiniPAM Debug Information')
  console.log('Debug Mode:', debugMode.value)
  console.log('API URL:', import.meta.env.VITE_API_URL || '/api')
  console.log('API Log Level:', import.meta.env.VITE_API_LOG_LEVEL)
  console.log('Current CIDR Count:', cidrs.value.length)
  console.log('Health Status:', healthStatus.value)
  console.log('Environment:', import.meta.env)
  console.groupEnd()
}
</script>
