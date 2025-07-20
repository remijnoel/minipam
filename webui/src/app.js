// MiniPAM Vue.js Application - Fixed version with working tree
const { createApp, ref, reactive, computed, onMounted } = Vue;

// API Service (same as before)
const apiService = {
  baseURL: '/api/v1',
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Network error' }));
        throw new Error(error.detail || error.message || `HTTP ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },
  
  async getCidrs() {
    return await this.request('/cidrs');
  },
  
  async getCidr(cidr) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`);
  },
  
  async createCidr(data) {
    return await this.request('/cidrs', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async updateCidr(cidr, data) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  async deleteCidr(cidr) {
    return await this.request(`/cidrs/${encodeURIComponent(cidr)}`, {
      method: 'DELETE'
    });
  },
  
  async getCidrTree() {
    return await this.request('/cidrs/tree');
  },
  
  async getHealth() {
    return await this.request('/health/ready');
  }
};

// Toast component
const Toast = {
  props: ['message', 'type', 'id'],
  emits: ['remove'],
  template: `
    <div :class="['toast', type]">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span>{{ message }}</span>
        <button @click="$emit('remove', id)" class="modal-close" style="margin-left: 1rem;">&times;</button>
      </div>
    </div>
  `,
  mounted() {
    setTimeout(() => {
      this.$emit('remove', this.id);
    }, 5000);
  }
};

// CIDR Modal component
const CidrModal = {
  props: ['show', 'cidr', 'mode', 'parentCidr'],
  emits: ['close', 'save'],
  data() {
    return {
      form: {
        cidr: '',
        name: '',
        description: '',
        parent: '',
        vlan: '',
        vrf: '',
        device: '',
        customer: '',
        location: '',
        tags: ''
      },
      errors: {},
      loading: false
    };
  },
  computed: {
    title() {
      if (this.mode === 'edit') {
        return 'Edit CIDR Block';
      }
      return this.parentCidr ? `Create Child CIDR (under ${this.parentCidr})` : 'Create CIDR Block';
    },
    isEdit() {
      return this.mode === 'edit';
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.resetForm();
        if (this.isEdit && this.cidr) {
          this.loadCidrData();
        }
      }
    }
  },
  methods: {
    resetForm() {
      this.form = {
        cidr: '',
        name: '',
        description: '',
        parent: this.parentCidr || '',
        vlan: '',
        vrf: '',
        device: '',
        customer: '',
        location: '',
        tags: ''
      };
      this.errors = {};
    },
    
    async loadCidrData() {
      if (!this.cidr) return;
      
      this.form.cidr = this.cidr.cidr;
      this.form.name = this.cidr.name || '';
      this.form.description = this.cidr.description || '';
      this.form.parent = this.cidr.parent || '';
      
      // Extract special tags
      const tags = this.cidr.tags || [];
      this.form.vlan = this.getTagValue(tags, 'vlan') || '';
      this.form.vrf = this.getTagValue(tags, 'vrf') || '';
      this.form.device = this.getTagValue(tags, 'device') || '';
      this.form.customer = this.getTagValue(tags, 'customer') || '';
      this.form.location = this.getTagValue(tags, 'location') || '';
      
      // Get remaining tags (excluding the special ones)
      const specialTags = ['vlan:', 'vrf:', 'device:', 'customer:', 'location:'];
      const otherTags = tags.filter(tag => 
        !specialTags.some(prefix => tag.toLowerCase().startsWith(prefix))
      );
      this.form.tags = otherTags.join(', ');
    },
    
    getTagValue(tags, key) {
      if (!tags || !Array.isArray(tags)) return null;
      const tag = tags.find(t => t.toLowerCase().startsWith(key.toLowerCase() + ':'));
      return tag ? tag.split(':')[1]?.trim() : null;
    },
    
    validateForm() {
      this.errors = {};
      
      if (!this.form.cidr.trim()) {
        this.errors.cidr = 'CIDR is required';
      }
      
      if (!this.form.name.trim()) {
        this.errors.name = 'Name is required';
      }
      
      return Object.keys(this.errors).length === 0;
    },
    
    async handleSave() {
      if (!this.validateForm()) return;
      
      this.loading = true;
      try {
        // Build tags array from special fields and general tags
        const tags = [];
        
        if (this.form.vlan) tags.push(`vlan:${this.form.vlan}`);
        if (this.form.vrf) tags.push(`vrf:${this.form.vrf}`);
        if (this.form.device) tags.push(`device:${this.form.device}`);
        if (this.form.customer) tags.push(`customer:${this.form.customer}`);
        if (this.form.location) tags.push(`location:${this.form.location}`);
        
        // Add other tags
        if (this.form.tags) {
          const otherTags = this.form.tags.split(',').map(t => t.trim()).filter(t => t);
          tags.push(...otherTags);
        }
        
        const data = {
          cidr: this.form.cidr,
          name: this.form.name,
          description: this.form.description || null,
          parent: this.form.parent || null,
          tags: tags
        };
        
        this.$emit('save', data);
      } catch (error) {
        console.error('Save error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    handleClose() {
      this.$emit('close');
    }
  },
  template: `
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">{{ title }}</h3>
          <button @click="handleClose" class="modal-close">&times;</button>
        </div>
        
        <form @submit.prevent="handleSave">
          <div class="form-group">
            <label class="form-label">CIDR Block *</label>
            <input 
              v-model="form.cidr" 
              :disabled="isEdit"
              type="text" 
              class="form-input" 
              placeholder="e.g., 10.0.0.0/16"
              :class="{ 'error': errors.cidr }"
            />
            <div v-if="errors.cidr" class="error-message">{{ errors.cidr }}</div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Name *</label>
            <input 
              v-model="form.name" 
              type="text" 
              class="form-input" 
              placeholder="e.g., Corporate Network"
              :class="{ 'error': errors.name }"
            />
            <div v-if="errors.name" class="error-message">{{ errors.name }}</div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Description</label>
            <input 
              v-model="form.description" 
              type="text" 
              class="form-input" 
              placeholder="Optional description"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Parent CIDR</label>
            <input 
              v-model="form.parent" 
              :disabled="!!parentCidr"
              type="text" 
              class="form-input" 
              placeholder="e.g., 10.0.0.0/8 (leave empty for root)"
            />
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label class="form-label">VLAN</label>
              <input 
                v-model="form.vlan" 
                type="text" 
                class="form-input" 
                placeholder="e.g., Default, 100"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">VRF</label>
              <input 
                v-model="form.vrf" 
                type="text" 
                class="form-input" 
                placeholder="e.g., Default, mgmt"
              />
            </div>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div class="form-group">
              <label class="form-label">Device</label>
              <input 
                v-model="form.device" 
                type="text" 
                class="form-input" 
                placeholder="e.g., switch01"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Customer</label>
              <input 
                v-model="form.customer" 
                type="text" 
                class="form-input" 
                placeholder="e.g., Acme Corp"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Location</label>
              <input 
                v-model="form.location" 
                type="text" 
                class="form-input" 
                placeholder="e.g., DC1, Office"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Additional Tags</label>
            <input 
              v-model="form.tags" 
              type="text" 
              class="form-input" 
              placeholder="e.g., production, dmz (comma-separated)"
            />
          </div>
          
          <div style="display: flex; justify-content: end; gap: 1rem; margin-top: 1.5rem;">
            <button type="button" @click="handleClose" class="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" :disabled="loading" class="btn btn-primary">
              {{ loading ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  `
};

// Main Application
const App = {
  components: {
    Toast,
    CidrModal
  },
  setup() {
    // Data
    const currentView = ref('tree');
    const loading = ref(false);
    const cidrs = ref([]);
    const cidrTree = ref([]);
    const health = ref(null);
    const selectedCidr = ref(null);
    
    // UI State
    const showModal = ref(false);
    const modalMode = ref('create');
    const editingCidr = ref(null);
    const parentCidr = ref(null);
    const expandedNodes = reactive({});
    
    // Search/Filter
    const searchQuery = ref('');
    
    // Toast notifications
    const toasts = ref([]);
    const toastId = ref(0);
    
    // Computed - Flatten tree for rendering
    const flattenedTree = computed(() => {
      const result = [];
      
      const flatten = (nodes, depth = 0, parentExpanded = true) => {
        if (!parentExpanded) return;
        
        nodes.forEach(node => {
          const isExpanded = expandedNodes[node.cidr] !== undefined ? expandedNodes[node.cidr] : depth < 2;
          result.push({
            ...node,
            depth,
            isExpanded,
            hasChildren: node.children && node.children.length > 0
          });
          
          if (node.children && node.children.length > 0) {
            flatten(node.children, depth + 1, isExpanded);
          }
        });
      };
      
      flatten(cidrTree.value);
      return result;
    });
    
    // Methods
    const loadData = async () => {
      loading.value = true;
      try {
        const [cidrsData, treeData, healthData] = await Promise.all([
          apiService.getCidrs(),
          apiService.getCidrTree(),
          apiService.getHealth()
        ]);
        
        cidrs.value = cidrsData.blocks || [];
        cidrTree.value = treeData;
        health.value = healthData;
        
        console.log('Loaded tree:', treeData);
      } catch (error) {
        showToast('Failed to load data: ' + error.message, 'error');
      } finally {
        loading.value = false;
      }
    };
    
    const toggleNode = (cidr) => {
      expandedNodes[cidr] = !expandedNodes[cidr];
    };
    
    const openCreateModal = () => {
      modalMode.value = 'create';
      editingCidr.value = null;
      parentCidr.value = null;
      showModal.value = true;
    };
    
    const openCreateChildModal = (cidr) => {
      modalMode.value = 'create';
      editingCidr.value = null;
      parentCidr.value = cidr;
      showModal.value = true;
    };
    
    const openEditModal = (node) => {
      modalMode.value = 'edit';
      editingCidr.value = node;
      showModal.value = true;
    };
    
    const closeModal = () => {
      showModal.value = false;
      editingCidr.value = null;
      parentCidr.value = null;
    };
    
    const saveCidr = async (data) => {
      try {
        if (modalMode.value === 'edit') {
          await apiService.updateCidr(editingCidr.value.cidr, data);
          showToast('CIDR updated successfully', 'success');
        } else {
          await apiService.createCidr(data);
          showToast('CIDR created successfully', 'success');
        }
        
        closeModal();
        await loadData();
      } catch (error) {
        showToast('Failed to save CIDR: ' + error.message, 'error');
      }
    };
    
    const deleteCidr = async (cidr) => {
      if (!confirm(`Are you sure you want to delete ${cidr}?`)) {
        return;
      }
      
      try {
        await apiService.deleteCidr(cidr);
        showToast('CIDR deleted successfully', 'success');
        await loadData();
      } catch (error) {
        showToast('Failed to delete CIDR: ' + error.message, 'error');
      }
    };
    
    const showToast = (message, type = 'info') => {
      const id = ++toastId.value;
      toasts.value.push({ id, message, type });
    };
    
    const removeToast = (id) => {
      const index = toasts.value.findIndex(t => t.id === id);
      if (index > -1) {
        toasts.value.splice(index, 1);
      }
    };
    
    // Helper function to get tag values
    const getTagValue = (tags, key) => {
      if (!tags || !Array.isArray(tags)) return null;
      const tag = tags.find(t => t.toLowerCase().startsWith(key.toLowerCase() + ':'));
      return tag ? tag.split(':')[1]?.trim() : null;
    };
    
    // Helper function to determine CIDR class for styling
    const getCidrClass = (node) => {
      if (!node.parent) return 'cidr-root';
      if (node.hasChildren) return 'cidr-parent';
      return 'cidr-leaf';
    };
    
    // Load data on mount
    onMounted(() => {
      loadData();
    });
    
    return {
      currentView,
      loading,
      cidrs,
      cidrTree,
      health,
      selectedCidr,
      showModal,
      modalMode,
      editingCidr,
      parentCidr,
      expandedNodes,
      searchQuery,
      toasts,
      flattenedTree,
      toggleNode,
      openCreateModal,
      openCreateChildModal,
      openEditModal,
      closeModal,
      saveCidr,
      deleteCidr,
      showToast,
      removeToast,
      getTagValue,
      getCidrClass
    };
  },
  template: `
    <div>
      <!-- Header -->
      <header class="header">
        <div class="container">
          <h1>MiniPAM</h1>
        </div>
      </header>
      
      <!-- Navigation -->
      <nav class="nav">
        <div class="container">
          <ul class="nav-tabs">
            <li>
              <a href="#" @click.prevent="currentView = 'dashboard'" 
                 :class="['nav-tab', { active: currentView === 'dashboard' }]">
                Dashboard
              </a>
            </li>
            <li>
              <a href="#" @click.prevent="currentView = 'tree'" 
                 :class="['nav-tab', { active: currentView === 'tree' }]">
                CIDR
              </a>
            </li>
          </ul>
        </div>
      </nav>
      
      <!-- Main Content -->
      <main class="main">
        <div class="container">
          <!-- Tree View -->
          <div v-if="currentView === 'tree'">
            <div class="card">
              <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 1rem;">
                <h2>CIDR Management</h2>
                <button @click="openCreateModal()" class="btn btn-primary">
                  + Create CIDR Block
                </button>
              </div>
              
              <div v-if="loading" style="text-align: center; padding: 2rem; color: #666;">
                Loading...
              </div>
              
              <div v-else-if="flattenedTree.length === 0">
                <p style="color: #666; text-align: center; padding: 2rem;">
                  No CIDR blocks found.
                  <a href="#" @click.prevent="openCreateModal()">Create your first one</a>.
                </p>
              </div>
              
              <div v-else class="cidr-table">
                <table class="table">
                  <thead>
                    <tr>
                      <th class="subnet-col">Subnet</th>
                      <th class="description-col">Description</th>
                      <th class="vlan-col">VLAN</th>
                      <th class="vrf-col">VRF</th>
                      <th class="master-col">Master Subnet</th>
                      <th class="device-col">Device</th>
                      <th class="customer-col">Customer</th>
                      <th class="location-col">Subnet Location</th>
                      <th class="actions-col">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="node in flattenedTree" :key="node.cidr" 
                        :class="{
                          'tree-row': true,
                          'has-children': node.hasChildren,
                          'expanded': node.isExpanded,
                          'collapsed': node.hasChildren && !node.isExpanded
                        }"
                        :style="{ '--depth': node.depth }">
                      
                      <!-- Subnet column with hierarchy -->
                      <td class="subnet-cell">
                        <div class="subnet-content" :style="{ paddingLeft: (node.depth * 1.5) + 'rem' }">
                          <span 
                            class="tree-toggle" 
                            @click="toggleNode(node.cidr)"
                            v-if="node.hasChildren"
                          >
                            {{ node.isExpanded ? '▼' : '▶' }}
                          </span>
                          <span v-else class="tree-spacer"></span>
                          
                          <span class="cidr-badge" :class="getCidrClass(node)">
                            {{ node.cidr }}
                          </span>
                          
                          <span class="cidr-name">{{ node.name }}</span>
                        </div>
                      </td>
                      
                      <!-- Description -->
                      <td class="description-cell">
                        {{ node.description || '-' }}
                      </td>
                      
                      <!-- VLAN -->
                      <td class="vlan-cell">
                        {{ getTagValue(node.tags, 'vlan') || 'Default' }}
                      </td>
                      
                      <!-- VRF -->
                      <td class="vrf-cell">
                        {{ getTagValue(node.tags, 'vrf') || 'Default' }}
                      </td>
                      
                      <!-- Master Subnet -->
                      <td class="master-cell">
                        <span v-if="node.parent" class="parent-cidr">{{ node.parent }}</span>
                        <span v-else>-</span>
                      </td>
                      
                      <!-- Device -->
                      <td class="device-cell">
                        {{ getTagValue(node.tags, 'device') || '-' }}
                      </td>
                      
                      <!-- Customer -->
                      <td class="customer-cell">
                        {{ getTagValue(node.tags, 'customer') || '-' }}
                      </td>
                      
                      <!-- Location -->
                      <td class="location-cell">
                        {{ getTagValue(node.tags, 'location') || '-' }}
                      </td>
                      
                      <!-- Actions -->
                      <td class="actions-cell">
                        <div class="action-buttons">
                          <button @click="openCreateChildModal(node.cidr)" 
                                  class="btn btn-mini btn-primary" 
                                  title="Add Child Subnet">
                            +
                          </button>
                          <button @click="openEditModal(node)" 
                                  class="btn btn-mini btn-secondary" 
                                  title="Edit">
                            ✎
                          </button>
                          <button @click="deleteCidr(node.cidr)" 
                                  class="btn btn-mini btn-danger" 
                                  title="Delete">
                            ×
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <!-- Dashboard View (placeholder) -->
          <div v-if="currentView === 'dashboard'">
            <div class="card">
              <h2>Dashboard</h2>
              <p>Dashboard features coming soon...</p>
            </div>
          </div>
        </div>
      </main>
      
      <!-- Modals -->
      <cidr-modal 
        :show="showModal"
        :cidr="editingCidr"
        :mode="modalMode"
        :parent-cidr="parentCidr"
        @close="closeModal"
        @save="saveCidr"
      />
      
      <!-- Toast Notifications -->
      <div class="toast-container">
        <toast 
          v-for="toast in toasts" 
          :key="toast.id"
          :id="toast.id"
          :message="toast.message"
          :type="toast.type"
          @remove="removeToast"
        />
      </div>
    </div>
  `
};

// Create and mount the app
createApp(App).mount('#app');