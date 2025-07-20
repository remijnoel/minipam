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
      this.form.tags = Array.isArray(this.cidr.tags) ? this.cidr.tags.join(', ') : '';
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
        const data = {
          cidr: this.form.cidr,
          name: this.form.name,
          description: this.form.description || null,
          parent: this.form.parent || null,
          tags: this.form.tags ? this.form.tags.split(',').map(t => t.trim()).filter(t => t) : []
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
          
          <div class="form-group">
            <label class="form-label">Tags</label>
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
      removeToast
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
              
              <div v-else class="tree">
                <div v-for="node in flattenedTree" :key="node.cidr">
                  <div 
                    class="tree-node" 
                    :style="{ paddingLeft: (node.depth * 2 + 0.5) + 'rem' }"
                  >
                    <span 
                      class="tree-toggle" 
                      @click="toggleNode(node.cidr)"
                      v-if="node.hasChildren"
                    >
                      {{ node.isExpanded ? '▼' : '▶' }}
                    </span>
                    <span v-else style="display: inline-block; width: 1rem;"></span>
                    
                    <span class="tree-content">
                      <strong>{{ node.cidr }}</strong>
                      <span style="color: #666; margin-left: 0.5rem;">{{ node.name }}</span>
                      <span 
                        v-if="node.tags && node.tags.length" 
                        style="color: #059669; margin-left: 0.5rem; font-size: 0.8rem;"
                      >
                        {{ node.tags.join(', ') }}
                      </span>
                    </span>
                    
                    <span style="margin-left: auto; display: flex; gap: 0.25rem;">
                      <button @click="openCreateChildModal(node.cidr)" class="btn btn-primary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                        + Child
                      </button>
                      <button @click="openEditModal(node)" class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                        Edit
                      </button>
                      <button @click="deleteCidr(node.cidr)" class="btn btn-danger" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;">
                        Delete
                      </button>
                    </span>
                  </div>
                </div>
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