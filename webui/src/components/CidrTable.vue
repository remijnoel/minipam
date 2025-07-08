<template>
  <div class="bg-white shadow overflow-hidden sm:rounded-md">
    <!-- Search and Filter Bar -->
    <div class="px-4 py-4 border-b border-gray-200 sm:px-6">
      <div class="flex items-center justify-between">
        <div class="flex-1 max-w-lg">
          <label for="search" class="sr-only">Search CIDR blocks</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              id="search"
              v-model="searchQuery"
              class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Search CIDR blocks..."
              type="search"
            />
          </div>
        </div>
        
        <!-- Expand/Collapse Controls -->
        <div class="ml-4 flex items-center space-x-2">
          <button
            @click="expandAll"
            class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            title="Expand all rows"
          >
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            Expand All
          </button>
          
          <button
            @click="collapseAll"
            class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            title="Collapse all rows"
          >
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 11l3-3m0 0l3 3m-3-3v8m0-13a9 9 0 110 18 9 9 0 010-18z" />
            </svg>
            Collapse All
          </button>
        </div>
        
        <div class="ml-4 text-sm text-gray-500">
          {{ visibleCidrs.length }} visible of {{ filteredCidrs.length }} filtered ({{ cidrs.length }} total)
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="px-4 py-8 text-center">
      <div class="inline-flex items-center">
        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span class="text-gray-500">Loading CIDR blocks...</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="visibleCidrs.length === 0" class="px-4 py-8 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No CIDR blocks visible</h3>
      <p class="mt-1 text-sm text-gray-500">
        {{ searchQuery ? 'Try adjusting your search criteria or expanding parent rows.' : 'Get started by creating a new CIDR block.' }}
      </p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              CIDR Block
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Description
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tags
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Parent
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th scope="col" class="relative px-6 py-3">
              <span class="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="cidr in visibleCidrs" :key="cidr.cidr" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <!-- Indentation based on hierarchy level -->
                <div v-if="cidr.level > 0" 
                     class="flex items-center" 
                     :style="`margin-left: ${cidr.level * 20}px`">
                  <svg class="w-4 h-4 text-gray-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7l3-3 3 3m0 6l-3 3-3-3" />
                  </svg>
                </div>
                
                <!-- Expand/Collapse button for parents -->
                <button
                  v-if="cidr.hasChildren"
                  @click="toggleExpanded(cidr.cidr)"
                  class="flex items-center mr-2 p-1 rounded hover:bg-gray-200 transition-colors"
                  :title="expandedRows.has(cidr.cidr) ? 'Collapse' : 'Expand'"
                >
                  <svg 
                    class="w-4 h-4 text-gray-600 transition-transform"
                    :class="{ 'rotate-90': expandedRows.has(cidr.cidr) }"
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                
                <!-- Spacer for non-parent rows to maintain alignment -->
                <div v-else class="w-6 mr-2"></div>
                
                <div class="text-sm font-medium text-gray-900">{{ cidr.cidr }}</div>
              </div>
            </td>
            
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">{{ cidr.name || '-' }}</div>
            </td>
            
            <td class="px-6 py-4">
              <div class="text-sm text-gray-900 max-w-xs truncate" :title="cidr.description">
                {{ cidr.description || '-' }}
              </div>
            </td>
            
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="(value, key) in cidr.tags || {}"
                  :key="key"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {{ key }}={{ value }}
                </span>
                <span v-if="!cidr.tags || Object.keys(cidr.tags).length === 0" class="text-sm text-gray-400">
                  No tags
                </span>
              </div>
            </td>
            
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <div class="space-y-1">
                <div v-if="cidr.parent" class="flex items-center">
                  <svg class="w-3 h-3 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                  <span class="text-xs">{{ cidr.parent }}</span>
                </div>
                <span v-if="!cidr.parent" class="text-gray-400 text-xs">
                  No parent
                </span>
              </div>
            </td>
            
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDate(cidr.created_at) }}
            </td>
            
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <div class="flex items-center space-x-2">
                <button
                  @click="$emit('view', cidr)"
                  class="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50"
                  title="View details"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                
                <button
                  @click="$emit('createChild', cidr)"
                  class="text-green-600 hover:text-green-900 p-1 rounded hover:bg-green-50"
                  title="Create child CIDR"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
                
                <button
                  @click="$emit('edit', cidr)"
                  class="text-yellow-600 hover:text-yellow-900 p-1 rounded hover:bg-yellow-50"
                  title="Edit"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                
                <button
                  @click="$emit('delete', cidr)"
                  class="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50"
                  title="Delete"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  cidrs: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
defineEmits(['view', 'edit', 'delete', 'createChild'])

// Reactive state
const searchQuery = ref('')
const expandedRows = ref(new Set())

// Helper function to get all children of a CIDR
function getChildren(parentCidr, cidrs) {
  return cidrs.filter(cidr => cidr.parent === parentCidr)
}

// Helper function to get all descendants of a CIDR (children, grandchildren, etc.)
function getAllDescendants(parentCidr, cidrs) {
  const descendants = []
  const children = getChildren(parentCidr, cidrs)
  
  for (const child of children) {
    descendants.push(child)
    descendants.push(...getAllDescendants(child.cidr, cidrs))
  }
  
  return descendants
}

// Toggle expand/collapse state
function toggleExpanded(cidrId) {
  if (expandedRows.value.has(cidrId)) {
    expandedRows.value.delete(cidrId)
  } else {
    expandedRows.value.add(cidrId)
  }
}

// Expand all CIDRs that have children
function expandAll() {
  const parentsWithChildren = filteredCidrs.value
    .filter(cidr => cidr.hasChildren)
    .map(cidr => cidr.cidr)
  
  expandedRows.value = new Set(parentsWithChildren)
}

// Collapse all CIDRs
function collapseAll() {
  expandedRows.value.clear()
}

// Helper function to compare IP addresses for sorting
function compareIpAddresses(cidr1, cidr2) {
  // Extract IP parts from CIDRs (e.g., "192.168.1.0/24" -> [192, 168, 1, 0])
  const getIpParts = (cidr) => {
    const ip = cidr.split('/')[0]
    return ip.split('.').map(part => parseInt(part, 10))
  }
  
  const ip1Parts = getIpParts(cidr1.cidr)
  const ip2Parts = getIpParts(cidr2.cidr)
  
  // Compare each octet
  for (let i = 0; i < 4; i++) {
    if (ip1Parts[i] !== ip2Parts[i]) {
      return ip1Parts[i] - ip2Parts[i]
    }
  }
  
  // If IPs are equal, compare subnet mask length
  const mask1 = parseInt(cidr1.cidr.split('/')[1], 10)
  const mask2 = parseInt(cidr2.cidr.split('/')[1], 10)
  return mask1 - mask2
}

// Helper function to create hierarchical structure
function buildCidrHierarchy(cidrs) {
  // First, sort by IP numerically
  const sortedCidrs = [...cidrs].sort(compareIpAddresses)
  
  // Map of CIDR to its level and processed state
  const cidrMap = new Map()
  
  // Initialize each CIDR's level (indentation level)
  sortedCidrs.forEach(cidr => {
    const children = getChildren(cidr.cidr, sortedCidrs)
    cidrMap.set(cidr.cidr, { 
      ...cidr, 
      level: 0, // Default level
      isChild: !!cidr.parent, // Is this a child?
      hasChildren: children.length > 0, // Does this have children?
      children: children
    })
  })
  
  // Set correct levels (we only need to do one pass because we only care about direct parent-child)
  sortedCidrs.forEach(cidr => {
    if (cidr.parent) {
      const cidrInfo = cidrMap.get(cidr.cidr)
      // Set level to parent's level + 1
      const parentInfo = cidrMap.get(cidr.parent)
      if (parentInfo) {
        cidrInfo.level = parentInfo.level + 1
      }
    }
  })
  
  // Convert back to array with level information
  return Array.from(cidrMap.values())
}

// Computed
const filteredCidrs = computed(() => {
  // First filter based on search query
  const filtered = !searchQuery.value ? props.cidrs : props.cidrs.filter(cidr => {
    const query = searchQuery.value.toLowerCase()
    return (
      cidr.cidr.toLowerCase().includes(query) ||
      (cidr.name && cidr.name.toLowerCase().includes(query)) ||
      (cidr.description && cidr.description.toLowerCase().includes(query)) ||
      (cidr.tags && Object.entries(cidr.tags).some(([key, value]) => 
        key.toLowerCase().includes(query) || value.toLowerCase().includes(query)
      ))
    )
  })
  
  // Then build hierarchical structure
  return buildCidrHierarchy(filtered)
})

const visibleCidrs = computed(() => {
  const result = []
  
  for (const cidr of filteredCidrs.value) {
    // Always show root level CIDRs (no parent)
    if (!cidr.parent) {
      result.push(cidr)
      continue
    }
    
    // For child CIDRs, check if all ancestors are expanded
    let shouldShow = true
    let currentParent = cidr.parent
    
    while (currentParent && shouldShow) {
      // If this parent is not expanded, don't show this child
      if (!expandedRows.value.has(currentParent)) {
        shouldShow = false
        break
      }
      
      // Find the parent's parent
      const parentCidr = filteredCidrs.value.find(c => c.cidr === currentParent)
      currentParent = parentCidr?.parent
    }
    
    if (shouldShow) {
      result.push(cidr)
    }
  }
  
  return result
})

// Methods
function formatDate(dateString) {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
