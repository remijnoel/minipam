<template>
  <!-- Modal Overlay -->
  <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('close')"></div>

      <!-- Modal content -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
        <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
          <!-- Header -->
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">
                CIDR Block Details
              </h3>
              <p class="mt-1 text-sm text-gray-500">
                {{ cidr.cidr }}
              </p>
            </div>
            <div class="flex space-x-2">
              <button
                @click="$emit('edit', cidr)"
                class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
              </button>
              <button
                @click="$emit('close')"
                class="inline-flex items-center p-2 border border-transparent rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Content -->
          <div class="space-y-6">
            <!-- Basic Information -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">CIDR Block</label>
                <div class="p-3 bg-gray-50 rounded-md border">
                  <span class="font-mono text-lg text-gray-900">{{ cidr.cidr }}</span>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <div class="p-3 bg-gray-50 rounded-md border">
                  <span class="text-gray-900">{{ cidr.name || 'No name set' }}</span>
                </div>
              </div>
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <div class="p-3 bg-gray-50 rounded-md border min-h-[4rem]">
                <span class="text-gray-900 whitespace-pre-wrap">{{ cidr.description || 'No description provided' }}</span>
              </div>
            </div>

            <!-- Network Information -->
            <div class="bg-blue-50 rounded-lg p-4">
              <h4 class="text-sm font-medium text-blue-900 mb-3">Network Information</h4>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span class="text-blue-700 font-medium">Network:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.network }}</div>
                </div>
                <div>
                  <span class="text-blue-700 font-medium">Subnet Mask:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.subnetMask }}</div>
                </div>
                <div>
                  <span class="text-blue-700 font-medium">Total IPs:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.totalIPs }}</div>
                </div>
                <div>
                  <span class="text-blue-700 font-medium">Usable IPs:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.usableIPs }}</div>
                </div>
                <div>
                  <span class="text-blue-700 font-medium">First IP:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.firstIP }}</div>
                </div>
                <div>
                  <span class="text-blue-700 font-medium">Last IP:</span>
                  <div class="font-mono text-blue-900">{{ networkInfo.lastIP }}</div>
                </div>
              </div>
            </div>

            <!-- Tags -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <div v-if="cidr.tags && Object.keys(cidr.tags).length > 0" class="flex flex-wrap gap-2">
                <span
                  v-for="(value, key) in cidr.tags"
                  :key="key"
                  class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                >
                  <span class="font-medium">{{ key }}</span>
                  <span class="mx-1">=</span>
                  <span>{{ value }}</span>
                </span>
              </div>
              <div v-else class="p-3 bg-gray-50 rounded-md border">
                <span class="text-gray-500 italic">No tags assigned</span>
              </div>
            </div>

            <!-- Hierarchy -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Parent -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Parent CIDR</label>
                <div v-if="cidr.parent" class="p-3 bg-green-50 rounded-md border border-green-200">
                  <div class="flex items-center">
                    <svg class="w-4 h-4 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                    <span class="font-mono text-green-900">{{ cidr.parent }}</span>
                  </div>
                </div>
                <div v-else class="p-3 bg-gray-50 rounded-md border">
                  <span class="text-gray-500 italic">No parent CIDR</span>
                </div>
              </div>
            </div>

            <!-- Metadata -->
            <div class="border-t pt-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Metadata</label>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-600">Created:</span>
                  <div class="font-medium text-gray-900">{{ formatDate(cidr.created_at) }}</div>
                </div>
                <div>
                  <span class="text-gray-600">Last Modified:</span>
                  <div class="font-medium text-gray-900">{{ formatDate(cidr.updated_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
          <button
            @click="$emit('close')"
            class="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:w-auto sm:text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  cidr: {
    type: Object,
    required: true
  },
  show: {
    type: Boolean,
    default: false
  }
})

// Emits
defineEmits(['close', 'edit'])

// Computed
const networkInfo = computed(() => {
  const cidr = props.cidr.cidr
  if (!cidr) return {}

  try {
    const [ip, prefixLength] = cidr.split('/')
    const prefix = parseInt(prefixLength)
    
    // Calculate network information
    const ipParts = ip.split('.').map(Number)
    const hostBits = 32 - prefix
    const totalIPs = Math.pow(2, hostBits)
    const usableIPs = totalIPs > 2 ? totalIPs - 2 : totalIPs
    
    // Calculate subnet mask
    const mask = (0xFFFFFFFF << hostBits) >>> 0
    const subnetMask = [
      (mask >>> 24) & 0xFF,
      (mask >>> 16) & 0xFF,
      (mask >>> 8) & 0xFF,
      mask & 0xFF
    ].join('.')
    
    // Calculate network address
    const networkInt = (ipParts[0] << 24 | ipParts[1] << 16 | ipParts[2] << 8 | ipParts[3]) & mask
    const network = [
      (networkInt >>> 24) & 0xFF,
      (networkInt >>> 16) & 0xFF,
      (networkInt >>> 8) & 0xFF,
      networkInt & 0xFF
    ].join('.')
    
    // Calculate first and last IP
    const firstIPInt = networkInt + (totalIPs > 2 ? 1 : 0)
    const lastIPInt = networkInt + totalIPs - (totalIPs > 2 ? 2 : 1)
    
    const firstIP = [
      (firstIPInt >>> 24) & 0xFF,
      (firstIPInt >>> 16) & 0xFF,
      (firstIPInt >>> 8) & 0xFF,
      firstIPInt & 0xFF
    ].join('.')
    
    const lastIP = [
      (lastIPInt >>> 24) & 0xFF,
      (lastIPInt >>> 16) & 0xFF,
      (lastIPInt >>> 8) & 0xFF,
      lastIPInt & 0xFF
    ].join('.')
    
    return {
      network,
      subnetMask,
      totalIPs: totalIPs.toLocaleString(),
      usableIPs: usableIPs.toLocaleString(),
      firstIP,
      lastIP
    }
  } catch (error) {
    console.error('Error calculating network info:', error)
    return {
      network: 'Invalid',
      subnetMask: 'Invalid',
      totalIPs: 'Invalid',
      usableIPs: 'Invalid',
      firstIP: 'Invalid',
      lastIP: 'Invalid'
    }
  }
})

// Methods
function formatDate(dateString) {
  if (!dateString) return 'Not available'
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>
