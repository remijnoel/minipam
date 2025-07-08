<template>
  <!-- Modal Overlay -->
  <div v-if="show" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="$emit('cancel')"></div>

      <!-- Modal content -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
        <form @submit.prevent="handleSubmit">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="sm:flex sm:items-start">
              <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                  {{ isEditing ? 'Edit CIDR Block' : (isCreatingChild ? 'Create Child CIDR Block' : 'Create New CIDR Block') }}
                </h3>
                
                <!-- Form Error Message -->
                <div v-if="props.error" class="mb-4">
                  <div class="bg-red-50 border border-red-200 rounded-md p-3">
                    <div class="flex">
                      <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                      <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">
                          <span v-if="props.error.includes('CIDR block') || props.error.includes('should be assigned')">Validation Error</span>
                          <span v-else>Error</span>
                        </h3>
                        <div class="mt-1 text-sm text-red-700">
                          <p>{{ props.error }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="space-y-4">
                  <!-- CIDR Field -->
                  <div>
                    <label for="cidr" class="block text-sm font-medium text-gray-700">
                      CIDR Block <span class="text-red-500">*</span>
                    </label>
                    <input
                      id="cidr"
                      v-model="formData.cidr"
                      :disabled="isEditing"
                      type="text"
                      required
                      placeholder="e.g., 192.168.1.0/24"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>

                  <!-- Name Field -->
                  <div>
                    <label for="name" class="block text-sm font-medium text-gray-700">
                      Name
                    </label>
                    <input
                      id="name"
                      v-model="formData.name"
                      type="text"
                      placeholder="e.g., Production Network"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    />
                  </div>

                  <!-- Description Field -->
                  <div>
                    <label for="description" class="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <textarea
                      id="description"
                      v-model="formData.description"
                      rows="3"
                      placeholder="Optional description..."
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    ></textarea>
                  </div>

                  <!-- Tags Field -->
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Tags
                    </label>
                    
                    <!-- Existing Tags -->
                    <div v-if="tagEntries.length > 0" class="mb-3 flex flex-wrap gap-2">
                      <span
                        v-for="(tag, index) in tagEntries"
                        :key="index"
                        class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                      >
                        {{ tag.key }}={{ tag.value }}
                        <button
                          type="button"
                          @click="removeTag(index)"
                          class="ml-2 inline-flex items-center p-0.5 rounded-full text-blue-400 hover:text-blue-600"
                        >
                          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </span>
                    </div>

                    <!-- Add New Tag -->
                    <div class="flex space-x-2">
                      <input
                        v-model="newTag.key"
                        type="text"
                        placeholder="Key"
                        class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      />
                      <input
                        v-model="newTag.value"
                        type="text"
                        placeholder="Value"
                        class="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      />
                      <button
                        type="button"
                        @click="addTag"
                        :disabled="!newTag.key || !newTag.value"
                        class="px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Add
                      </button>
                    </div>
                  </div>

                  <!-- Parent CIDR Field -->
                  <div>
                    <label for="parent" class="block text-sm font-medium text-gray-700">
                      Parent CIDR
                      <span v-if="isCreatingChild" class="text-sm text-gray-500">(inherited from parent)</span>
                    </label>
                    <input
                      id="parent"
                      v-model="formData.parent"
                      :disabled="isCreatingChild"
                      type="text"
                      placeholder="e.g., 192.168.0.0/16"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Actions -->
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              {{ isEditing ? 'Update' : 'Create' }}
            </button>
            <button
              type="button"
              @click="$emit('cancel')"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// Props
const props = defineProps({
  cidr: {
    type: Object,
    default: null
  },
  show: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

// Emits
const emit = defineEmits(['save', 'cancel'])

// Computed
const isEditing = computed(() => !!props.cidr && !!props.cidr.cidr)
const isCreatingChild = computed(() => !!props.cidr && !!props.cidr.parent && !props.cidr.cidr)

// Reactive state
const formData = ref({
  cidr: '',
  name: '',
  description: '',
  tags: {},
  parent: ''
})

const newTag = ref({
  key: '',
  value: ''
})

const tagEntries = computed(() => {
  return Object.entries(formData.value.tags || {}).map(([key, value]) => ({ key, value }))
})

// Watch for prop changes
watch(() => props.cidr, (newCidr) => {
  if (newCidr) {
    formData.value = {
      cidr: newCidr.cidr || '',
      name: newCidr.name || '',
      description: newCidr.description || '',
      tags: { ...(newCidr.tags || {}) },
      parent: newCidr.parent || ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// Methods
function resetForm() {
  formData.value = {
    cidr: '',
    name: '',
    description: '',
    tags: {},
    parent: ''
  }
  newTag.value = { key: '', value: '' }
}

function addTag() {
  if (newTag.value.key && newTag.value.value) {
    formData.value.tags[newTag.value.key] = newTag.value.value
    newTag.value = { key: '', value: '' }
  }
}

function removeTag(index) {
  const entries = Object.entries(formData.value.tags)
  const [key] = entries[index]
  delete formData.value.tags[key]
}

function handleSubmit() {
  // Clean up the data before submitting
  const submitData = {
    cidr: formData.value.cidr,
    name: formData.value.name || null,
    description: formData.value.description || null,
    tags: Object.keys(formData.value.tags).length > 0 ? formData.value.tags : {},
    parent: formData.value.parent || null
  }

  // For child CIDR creation, ensure we keep the parent field
  if (isCreatingChild.value && submitData.parent) {
    // Keep parent as is - don't remove it even if null
  } else {
    // For regular create/update, remove empty values
    if (submitData.parent === null || submitData.parent === '') {
      submitData.parent = null
    }
  }

  // Remove null/empty values for create operations (except parent for child CIDRs)
  if (!isEditing.value) {
    Object.keys(submitData).forEach(key => {
      // Skip parent field for child CIDR creation
      if (key === 'parent' && isCreatingChild.value) {
        return
      }
      
      if (submitData[key] === null || submitData[key] === '') {
        delete submitData[key]
      }
    })
  }

  emit('save', submitData)
}
</script>
